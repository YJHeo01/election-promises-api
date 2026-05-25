from fastapi import FastAPI

from app.routers import answer_context, health, privacy


app = FastAPI(
    title="Election Promise Context API",
    description=(
        "Custom GPT Action backend that returns structured, source-backed "
        "election promise context without generating final answer text."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(privacy.router)
app.include_router(answer_context.router)

