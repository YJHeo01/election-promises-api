from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Candidate, Contest, Election, Material, PromiseChunk


BASE_URL = "https://policy.nec.go.kr"
SG_ID = "20260603"
ELECTION_ID = "election_9_local"
ELECTION_NAME = "제9회 전국동시지방선거"
ELECTION_DATE = date(2026, 6, 3)

TARGET_ELECTIONS = {
    "320260603": {
        "name": "시·도지사선거",
        "office": "광역단체장",
        "contest_prefix": "nec_governor",
    },
    "420260603": {
        "name": "구·시·군의 장선거",
        "office": "기초단체장",
        "contest_prefix": "nec_mayor",
    },
}

ENDPOINTS = {
    "region": "/plc/commiment/initUCACommimentRegion.do",
    "gu": "/plc/commiment/initUCACommimentGu.do",
    "sgg": "/plc/commiment/initUCACommimentSgg.do",
    "candidate_list": "/plc/commiment/initUCACommimentList.do",
    "promise_view": "/plc/commiment/UELPromisePopupView.do",
}


@dataclass
class Top5FileInfo:
    file_type: str
    pdf_path: str | None = None
    ocr_seq_no: str | None = None
    raw_parts: list[str] = field(default_factory=list)


@dataclass
class ParsedPromise:
    rank: int
    title: str
    text: str


@dataclass
class ScrapedCandidate:
    election_id: str
    election_name: str
    sub_sg_id: str
    sub_sg_name: str
    office: str
    region_id: str
    region_name: str
    contest_id: str
    contest_name: str
    contest_code: str
    sgg_id: str
    sgg_name: str
    candidate_id: str
    candidate_name: str
    party_id: str | None
    party_name: str | None
    candidate_number: str | None
    job: str | None
    education: str | None
    photo_path: str | None
    top5_file: Top5FileInfo | None
    promises: list[ParsedPromise]
    raw_candidate: dict[str, Any]
    raw_html_path: str | None = None
    fetched_at: str | None = None


class PolicyParagraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[dict[str, str]] = []
        self._current_p: dict[str, Any] | None = None
        self._current_h1_class: str | None = None
        self._h1_chunks: list[str] = []
        self.paragraphs: list[dict[str, str]] = []
        self.policy_title: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        self._stack.append({"tag": tag, "class": attr_map.get("class", "")})
        if tag == "p":
            self._current_p = {"class": attr_map.get("class", ""), "chunks": []}
        elif tag == "h1":
            self._current_h1_class = attr_map.get("class", "")
            self._h1_chunks = []
        elif tag == "br" and self._current_p is not None:
            self._current_p["chunks"].append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._current_p is not None:
            text = normalize_text("".join(self._current_p["chunks"]))
            self.paragraphs.append({"class": self._current_p["class"], "text": text})
            self._current_p = None
        elif tag == "h1" and self._current_h1_class is not None:
            if "policy-title" in self._current_h1_class:
                self.policy_title = normalize_text("".join(self._h1_chunks))
            self._current_h1_class = None
            self._h1_chunks = []

        if self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current_p is not None:
            self._current_p["chunks"].append(data)
        if self._current_h1_class is not None:
            self._h1_chunks.append(data)


def normalize_text(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def slug(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", "_", value.strip())
    return normalized.strip("_") or "unknown"


def request_json(client: httpx.Client, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"{BASE_URL}{endpoint}", data=data)
    response.raise_for_status()
    return response.json()


def request_text(client: httpx.Client, endpoint: str, data: dict[str, Any]) -> str:
    response = client.post(f"{BASE_URL}{endpoint}", data=data)
    response.raise_for_status()
    return response.text


def parse_fileinfo(value: str | None) -> list[Top5FileInfo]:
    if not value:
        return []

    files: list[Top5FileInfo] = []
    for item in value.split(","):
        parts = item.split("||")
        if not parts or not parts[0]:
            continue
        ocr_seq_no = None
        if len(parts) > 2 and parts[2].strip().isdigit():
            ocr_seq_no = parts[2].strip()
        files.append(
            Top5FileInfo(
                file_type=parts[0].strip(),
                pdf_path=parts[1].strip() if len(parts) > 1 and parts[1].strip() else None,
                ocr_seq_no=ocr_seq_no,
                raw_parts=parts,
            )
        )
    return files


def parse_promises_from_html(source: str) -> list[ParsedPromise]:
    parser = PolicyParagraphParser()
    parser.feed(source)

    promises: list[ParsedPromise] = []
    pending: tuple[int, str] | None = None
    for paragraph in parser.paragraphs:
        class_name = paragraph["class"]
        text = paragraph["text"]
        if not text:
            continue
        if "accordion-questions" in class_name:
            match = re.match(r"^\s*(\d+)\.\s*(.+)$", text, flags=re.S)
            if match is None:
                pending = (len(promises) + 1, text)
            else:
                pending = (int(match.group(1)), normalize_text(match.group(2)))
            continue

        if pending is not None:
            rank, title = pending
            promises.append(ParsedPromise(rank=rank, title=title, text=text))
            pending = None

    return promises


def save_raw_html(raw_dir: Path, ocr_seq_no: str, source: str) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ocr_seq_no}.html"
    path.write_text(source, encoding="utf-8")
    return path


def get_regions(client: httpx.Client, sub_sg_id: str) -> tuple[list[dict[str, Any]], str]:
    data = request_json(
        client,
        ENDPOINTS["region"],
        {"sgId": SG_ID, "subSgId": sub_sg_id},
    )
    return data.get("regionlist", []), data.get("typeinfo", {}).get("sgTypecode", "")


def get_gu_list(client: httpx.Client, sub_sg_id: str, region_id: str) -> list[dict[str, Any]]:
    data = request_json(
        client,
        ENDPOINTS["gu"],
        {
            "sgId": SG_ID,
            "subSgId": sub_sg_id,
            "wiwsidocode": region_id,
            "sortYn": "",
        },
    )
    return data.get("gulist", [])


def get_sgg_list(
    client: httpx.Client,
    sub_sg_id: str,
    region_id: str,
    gu_id: str,
) -> list[dict[str, Any]]:
    data = request_json(
        client,
        ENDPOINTS["sgg"],
        {
            "sgId": SG_ID,
            "subSgId": sub_sg_id,
            "wiwsidocode": region_id,
            "wiwid": gu_id,
            "sortYn": "",
        },
    )
    return data.get("sgglist", [])


def get_candidate_page(
    client: httpx.Client,
    sub_sg_id: str,
    region_id: str,
    sgg_id: str,
    sg_typecode: str,
    page_index: int,
) -> dict[str, Any]:
    return request_json(
        client,
        ENDPOINTS["candidate_list"],
        {
            "sgId": SG_ID,
            "subSgId": sub_sg_id,
            "hRegionId": region_id,
            "hGuId": "",
            "hSggId": sgg_id,
            "sgTypecode": sg_typecode,
            "pageIndex": str(page_index),
            "phGuId": "",
            "elecEndYn": "N",
        },
    )


def iter_candidates(
    client: httpx.Client,
    sub_sg_id: str,
    region_id: str,
    sgg_id: str,
    sg_typecode: str,
    delay: float,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    page_index = 1
    total_count = None

    while True:
        data = get_candidate_page(client, sub_sg_id, region_id, sgg_id, sg_typecode, page_index)
        page_candidates = data.get("list", [])
        candidates.extend(page_candidates)

        if total_count is None:
            total_count = int(data.get("totalCnt") or 0)
        if len(candidates) >= total_count or not page_candidates:
            return candidates

        page_index += 1
        time.sleep(delay)


def build_scraped_candidate(
    *,
    client: httpx.Client,
    raw_candidate: dict[str, Any],
    sub_sg_id: str,
    region_id: str,
    region_name: str,
    raw_dir: Path,
) -> ScrapedCandidate:
    election_meta = TARGET_ELECTIONS[sub_sg_id]
    top5_file = next(
        (file for file in parse_fileinfo(raw_candidate.get("fileinfo")) if file.file_type == "5대공약"),
        None,
    )

    promises: list[ParsedPromise] = []
    raw_html_path: str | None = None
    if top5_file and top5_file.ocr_seq_no:
        source = request_text(
            client,
            ENDPOINTS["promise_view"],
            {
                "ocrCnvrSeqNo": top5_file.ocr_seq_no,
                "menuName": ELECTION_NAME,
            },
        )
        raw_html_path = str(save_raw_html(raw_dir, top5_file.ocr_seq_no, source))
        promises = parse_promises_from_html(source)

    sgg_id = str(raw_candidate.get("sggid") or "")
    sgg_name = str(raw_candidate.get("sggname") or region_name)
    contest_code = f"{election_meta['contest_prefix']}_{sgg_id or slug(sgg_name)}"
    contest_id = f"contest_{contest_code}"
    contest_name = f"{sgg_name} {election_meta['name']}"

    return ScrapedCandidate(
        election_id=SG_ID,
        election_name=ELECTION_NAME,
        sub_sg_id=sub_sg_id,
        sub_sg_name=election_meta["name"],
        office=election_meta["office"],
        region_id=region_id,
        region_name=region_name,
        contest_id=contest_id,
        contest_name=contest_name,
        contest_code=contest_code,
        sgg_id=sgg_id,
        sgg_name=sgg_name,
        candidate_id=str(raw_candidate.get("huboid") or ""),
        candidate_name=str(raw_candidate.get("hbjname") or ""),
        party_id=raw_candidate.get("jdid"),
        party_name=raw_candidate.get("jdname"),
        candidate_number=raw_candidate.get("hbjgiho"),
        job=raw_candidate.get("hbjjikup"),
        education=raw_candidate.get("hbjhakruk"),
        photo_path=raw_candidate.get("filename"),
        top5_file=top5_file,
        promises=promises,
        raw_candidate=raw_candidate,
        raw_html_path=raw_html_path,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def _candidate_to_json(candidate: ScrapedCandidate) -> dict[str, Any]:
    return asdict(candidate)


def save_outputs(candidates: list[ScrapedCandidate], output: Path, jsonl_output: Path | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": BASE_URL,
        "electionId": SG_ID,
        "electionName": ELECTION_NAME,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(candidates),
        "candidates": [_candidate_to_json(candidate) for candidate in candidates],
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if jsonl_output is not None:
        jsonl_output.parent.mkdir(parents=True, exist_ok=True)
        with jsonl_output.open("w", encoding="utf-8") as file:
            for candidate in candidates:
                file.write(json.dumps(_candidate_to_json(candidate), ensure_ascii=False) + "\n")


def import_to_db(candidates: list[ScrapedCandidate]) -> None:
    init_db()
    db = SessionLocal()
    try:
        _import_to_db_session(db, candidates)
    finally:
        db.close()


def _import_to_db_session(db: Session, candidates: list[ScrapedCandidate]) -> None:
    db.merge(
        Election(
            id=ELECTION_ID,
            name=ELECTION_NAME,
            type="지방선거",
            election_date=ELECTION_DATE,
            source_code="NEC_LOCAL_9",
        )
    )

    seen_contests: set[str] = set()
    seen_candidates: set[str] = set()
    seen_materials: set[str] = set()

    for item in candidates:
        if item.contest_id not in seen_contests:
            db.merge(
                Contest(
                    id=item.contest_id,
                    election_id=ELECTION_ID,
                    name=item.contest_name,
                    region=item.sgg_name or item.region_name,
                    office=item.office,
                    code=item.contest_code,
                )
            )
            seen_contests.add(item.contest_id)

        candidate_id = f"nec_{item.candidate_id}"
        if candidate_id not in seen_candidates:
            db.merge(
                Candidate(
                    id=candidate_id,
                    election_id=ELECTION_ID,
                    contest_id=item.contest_id,
                    name=item.candidate_name,
                    party=item.party_name or "",
                    candidate_number=item.candidate_number,
                    external_id=item.candidate_id,
                )
            )
            seen_candidates.add(candidate_id)

        if item.top5_file is not None:
            material_id = f"nec_top5_{item.candidate_id}"
            local_path = item.raw_html_path
            if material_id not in seen_materials:
                db.merge(
                    Material(
                        id=material_id,
                        candidate_id=candidate_id,
                        type="official_top5_promises",
                        title=f"{item.candidate_name} 5대공약",
                        url=f"{BASE_URL}{ENDPOINTS['promise_view']}",
                        local_path=local_path,
                        text_extracted=bool(item.promises),
                        fetched_at=datetime.now(timezone.utc),
                    )
                )
                seen_materials.add(material_id)

            for promise in item.promises:
                text_hash = hashlib.sha1(  # noqa: S324 - stable content id only
                    f"{item.candidate_id}:{promise.rank}:{promise.title}".encode("utf-8")
                ).hexdigest()[:12]
                db.merge(
                    PromiseChunk(
                        id=f"nec_top5_{item.candidate_id}_{promise.rank}_{text_hash}",
                        candidate_id=candidate_id,
                        material_id=material_id,
                        category="핵심",
                        title=promise.title,
                        text=promise.text,
                        page=None,
                        chunk_index=promise.rank,
                    )
                )

    db.commit()


def load_scraped_candidates(path: Path) -> list[ScrapedCandidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates: list[ScrapedCandidate] = []
    for item in payload.get("candidates", []):
        top5_payload = item.get("top5_file")
        top5_file = Top5FileInfo(**top5_payload) if top5_payload else None
        promises = [ParsedPromise(**promise) for promise in item.get("promises", [])]
        candidates.append(
            ScrapedCandidate(
                election_id=item["election_id"],
                election_name=item["election_name"],
                sub_sg_id=item["sub_sg_id"],
                sub_sg_name=item["sub_sg_name"],
                office=item["office"],
                region_id=item["region_id"],
                region_name=item["region_name"],
                contest_id=item["contest_id"],
                contest_name=item["contest_name"],
                contest_code=item["contest_code"],
                sgg_id=item["sgg_id"],
                sgg_name=item["sgg_name"],
                candidate_id=item["candidate_id"],
                candidate_name=item["candidate_name"],
                party_id=item.get("party_id"),
                party_name=item.get("party_name"),
                candidate_number=item.get("candidate_number"),
                job=item.get("job"),
                education=item.get("education"),
                photo_path=item.get("photo_path"),
                top5_file=top5_file,
                promises=promises,
                raw_candidate=item.get("raw_candidate", {}),
                raw_html_path=item.get("raw_html_path"),
                fetched_at=item.get("fetched_at"),
            )
        )
    return candidates


def scrape(
    *,
    sub_sg_ids: list[str],
    region_filter: set[str] | None,
    output: Path,
    jsonl_output: Path | None,
    raw_dir: Path,
    save_db: bool,
    delay: float,
    limit_candidates: int | None,
) -> list[ScrapedCandidate]:
    results: list[ScrapedCandidate] = []
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for sub_sg_id in sub_sg_ids:
            if sub_sg_id not in TARGET_ELECTIONS:
                raise ValueError(f"Unsupported subSgId: {sub_sg_id}")

            regions, sg_typecode = get_regions(client, sub_sg_id)
            for region in regions:
                region_id = str(region.get("wiwid") or "")
                region_name = str(region.get("wiwname") or "")
                if region_filter and region_id not in region_filter and region_name not in region_filter:
                    continue

                if sg_typecode == "3":
                    candidates = iter_candidates(
                        client,
                        sub_sg_id,
                        region_id,
                        "",
                        sg_typecode,
                        delay,
                    )
                elif sg_typecode == "4":
                    sggs: list[dict[str, Any]] = []
                    for gu in get_gu_list(client, sub_sg_id, region_id):
                        gu_id = str(gu.get("wiwid") or "")
                        sggs.extend(get_sgg_list(client, sub_sg_id, region_id, gu_id))
                        time.sleep(delay)

                    candidates = []
                    seen_sgg_ids: set[str] = set()
                    for sgg in sggs:
                        sgg_id = str(sgg.get("sggid") or "")
                        if not sgg_id or sgg_id in seen_sgg_ids:
                            continue
                        seen_sgg_ids.add(sgg_id)
                        candidates.extend(
                            iter_candidates(
                                client,
                                sub_sg_id,
                                region_id,
                                sgg_id,
                                sg_typecode,
                                delay,
                            )
                        )
                        time.sleep(delay)
                else:
                    continue

                for raw_candidate in candidates:
                    if limit_candidates is not None and len(results) >= limit_candidates:
                        save_outputs(results, output, jsonl_output)
                        if save_db:
                            import_to_db(results)
                        return results

                    item = build_scraped_candidate(
                        client=client,
                        raw_candidate=raw_candidate,
                        sub_sg_id=sub_sg_id,
                        region_id=region_id,
                        region_name=region_name,
                        raw_dir=raw_dir,
                    )
                    results.append(item)
                    time.sleep(delay)

    save_outputs(results, output, jsonl_output)
    if save_db:
        import_to_db(results)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape NEC policy.nec.go.kr top-5 candidate promises.",
    )
    parser.add_argument(
        "--sub-sg-id",
        action="append",
        choices=sorted(TARGET_ELECTIONS),
        help="Target election type. Defaults to 시·도지사선거 and 구·시·군의 장선거.",
    )
    parser.add_argument(
        "--region",
        action="append",
        help="Region id or name to scrape, e.g. 2800 or 인천광역시. Can be repeated.",
    )
    parser.add_argument(
        "--output",
        default="data/nec_top5_promises.json",
        help="Parsed JSON output path.",
    )
    parser.add_argument(
        "--jsonl-output",
        default="data/nec_top5_promises.jsonl",
        help="Parsed JSONL output path. Pass empty string to skip.",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/nec_top5/raw_html",
        help="Directory for raw OCR HTML pages.",
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Also upsert scraped records into the application database.",
    )
    parser.add_argument(
        "--import-json",
        help="Import an existing scraped JSON output into the application database without scraping.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests in seconds.",
    )
    parser.add_argument(
        "--limit-candidates",
        type=int,
        default=None,
        help="Stop after this many candidates, useful for smoke tests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.import_json:
        candidates = load_scraped_candidates(Path(args.import_json))
        import_to_db(candidates)
        print(f"Imported {len(candidates)} candidates from {args.import_json} into the database.")
        return

    sub_sg_ids = args.sub_sg_id or list(TARGET_ELECTIONS)
    jsonl_output = Path(args.jsonl_output) if args.jsonl_output else None
    candidates = scrape(
        sub_sg_ids=sub_sg_ids,
        region_filter=set(args.region) if args.region else None,
        output=Path(args.output),
        jsonl_output=jsonl_output,
        raw_dir=Path(args.raw_dir),
        save_db=args.save_db,
        delay=args.delay,
        limit_candidates=args.limit_candidates,
    )
    print(f"Scraped {len(candidates)} candidates.")
    print(f"Saved JSON to {args.output}.")
    if jsonl_output is not None:
        print(f"Saved JSONL to {jsonl_output}.")
    if args.save_db:
        print("Imported scraped records into the database.")


if __name__ == "__main__":
    main()
