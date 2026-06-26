from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db, init_db, ping_db
from app.image_service import ImageGenerationError, generate_image
from app.llm_service import PromptOptimizeError, generate_idea, optimize_prompt
from app.models import Generation, PromptPreference
from app.prompt_service import compose_prompt, get_style_options, get_topic_options
from app.runtime_config import read_runtime_config, save_runtime_config
from app.schemas import (
    ComposeRequest,
    ComposeResponse,
    GenerateIdeaRequest,
    GenerateIdeaResponse,
    GenerateRequest,
    GenerateResponse,
    OptimizePromptRequest,
    PromptPreferenceRequest,
    RuntimeConfigResponse,
    RuntimeConfigUpdate,
)

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _get_preference(db: Session, topic: str, style: str) -> PromptPreference | None:
    return (
        db.query(PromptPreference)
        .filter(PromptPreference.topic == topic, PromptPreference.style == style)
        .one_or_none()
    )


def _save_preference(db: Session, topic: str, style: str, prompt: str, negative_prompt: str) -> PromptPreference:
    preference = _get_preference(db, topic, style)
    if preference:
        preference.prompt = prompt
        preference.negative_prompt = negative_prompt
    else:
        preference = PromptPreference(
            topic=topic,
            style=style,
            prompt=prompt,
            negative_prompt=negative_prompt,
        )
        db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def _prompt_payload(db: Session, topic: str, style: str, idea: str = "") -> dict[str, str | bool]:
    default_data = compose_prompt(topic, style, idea)
    preference = _get_preference(db, topic, style)
    if preference:
        return {
            "prompt": preference.prompt,
            "negative_prompt": preference.negative_prompt,
            "ratio": default_data["ratio"],
            "saved": True,
        }
    return {**default_data, "saved": False}


def render_index(history: list[Generation]) -> str:
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    topic_options = "".join(
        f'<option value="{item["id"]}" data-ratio="{item["ratio"]}">{item["name"]} · {item["ratio"]}</option>'
        for item in get_topic_options()
    )
    style_options = "".join(
        f'<option value="{item["id"]}">{item["name"]}</option>'
        for item in get_style_options()
    )
    if history:
        history_html = "".join(
            (
                f'<article class="history-item" data-id="{item.id}" '
                f'data-image="{_escape_attr(item.image_url)}" '
                f'data-prompt="{_escape_attr(item.prompt)}" '
                f'data-negative="{_escape_attr(item.negative_prompt)}">'
                f'<button class="history-preview" type="button" aria-label="预览生成记录 {item.id}">'
                f'<img src="{_escape_attr(item.image_url)}" alt="生成记录 {item.id}">'
                f'<span>{_escape_attr(item.idea)}</span>'
                f'</button>'
                f'<a class="history-download" href="/api/generations/{item.id}/download" download title="下载图片">下载</a>'
                f'</article>'
            )
            for item in history
        )
    else:
        history_html = '<div class="empty">暂无历史，先生成一张。</div>'
    return (
        template.replace("{{ provider }}", get_settings().image_provider)
        .replace("{{ history_count }}", str(len(history)))
        .replace("<!-- TOPIC_OPTIONS -->", topic_options)
        .replace("<!-- STYLE_OPTIONS -->", style_options)
        .replace("<!-- HISTORY_ITEMS -->", history_html)
    )


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
    except SQLAlchemyError as exc:
        message = (
            "MySQL connection failed. Update DATABASE_URL in .env and make sure the "
            "creative_workshop database exists. Original error: " + str(exc)
        )
        raise RuntimeError(message) from exc


@app.get("/", response_class=HTMLResponse)
def index(db: Session = Depends(get_db)):
    history = db.query(Generation).order_by(desc(Generation.id)).all()
    return HTMLResponse(render_index(history))


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "database": ping_db(), "provider": get_settings().image_provider}


@app.get("/api/config", response_model=RuntimeConfigResponse)
def get_runtime_config():
    return read_runtime_config()


@app.post("/api/config", response_model=RuntimeConfigResponse)
def update_runtime_config(payload: RuntimeConfigUpdate):
    return save_runtime_config(payload)


@app.get("/api/prompts/preference", response_model=ComposeResponse)
def get_prompt_preference(topic: str, style: str, idea: str = "", db: Session = Depends(get_db)):
    return _prompt_payload(db, topic, style, idea)


@app.post("/api/prompts/preference", response_model=ComposeResponse)
def save_prompt_preference(payload: PromptPreferenceRequest, db: Session = Depends(get_db)):
    default_data = compose_prompt(payload.topic, payload.style)
    preference = _save_preference(
        db,
        payload.topic,
        payload.style,
        payload.prompt.strip() or default_data["prompt"],
        payload.negative_prompt.strip() or default_data["negative_prompt"],
    )
    return {
        "prompt": preference.prompt,
        "negative_prompt": preference.negative_prompt,
        "ratio": default_data["ratio"],
        "saved": True,
    }


@app.post("/api/prompts/reset", response_model=ComposeResponse)
def reset_prompt_preference(payload: ComposeRequest, db: Session = Depends(get_db)):
    preference = _get_preference(db, payload.topic, payload.style)
    if preference:
        db.delete(preference)
        db.commit()
    default_data = compose_prompt(payload.topic, payload.style, payload.idea)
    return {**default_data, "saved": False}


@app.post("/api/prompts/optimize", response_model=ComposeResponse)
async def optimize_prompt_endpoint(payload: OptimizePromptRequest, db: Session = Depends(get_db)):
    default_data = compose_prompt(payload.topic, payload.style, payload.idea)
    try:
        optimized = await optimize_prompt(
            payload.topic,
            payload.style,
            payload.idea,
            payload.prompt.strip() or default_data["prompt"],
            payload.negative_prompt.strip() or default_data["negative_prompt"],
        )
    except PromptOptimizeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    preference = _save_preference(
        db,
        payload.topic,
        payload.style,
        optimized["prompt"],
        optimized["negative_prompt"],
    )
    return {
        "prompt": preference.prompt,
        "negative_prompt": preference.negative_prompt,
        "ratio": default_data["ratio"],
        "saved": True,
    }



@app.post("/api/ideas/generate", response_model=GenerateIdeaResponse)
async def generate_idea_endpoint(payload: GenerateIdeaRequest):
    try:
        idea = await generate_idea(payload.topic, payload.style)
    except PromptOptimizeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"idea": idea}


@app.post("/api/prompt/compose", response_model=ComposeResponse)
def compose(payload: ComposeRequest, db: Session = Depends(get_db)) -> dict[str, str | bool]:
    return _prompt_payload(db, payload.topic, payload.style, payload.idea)


@app.post("/api/image/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest, db: Session = Depends(get_db)) -> Generation:
    prompt_data = compose_prompt(payload.topic, payload.style, payload.idea)
    positive_keywords = (payload.prompt or prompt_data["prompt"]).strip()
    negative_keywords = (payload.negative_prompt or prompt_data["negative_prompt"]).strip()
    image_prompt = f"{payload.idea.strip()}，{positive_keywords}" if positive_keywords else payload.idea.strip()
    try:
        image_url, provider = await generate_image(
            image_prompt, negative_keywords, prompt_data["ratio"]
        )
        _save_preference(db, payload.topic, payload.style, positive_keywords, negative_keywords)
        record = Generation(
            topic=payload.topic,
            style=payload.style,
            idea=payload.idea,
            prompt=positive_keywords,
            negative_prompt=negative_keywords,
            image_url=image_url,
            provider=provider,
            status="success",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except ImageGenerationError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/generations/{generation_id}/download")
async def download_generation(generation_id: int, db: Session = Depends(get_db)):
    record = db.get(Generation, generation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found.")

    filename = f"creative-workshop-{record.id}.png"
    image_url = record.image_url

    if image_url.startswith("/static/generated/"):
        local_path = Path("app") / image_url.lstrip("/")
        if not local_path.exists():
            raise HTTPException(status_code=404, detail="Local image file not found.")
        return FileResponse(local_path, filename=local_path.name)

    if image_url.startswith("http://") or image_url.startswith("https://"):
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.get(image_url)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Failed to download remote image.")

        content_type = response.headers.get("content-type", "image/png").split(";")[0]
        suffix = Path(urlparse(image_url).path).suffix
        if suffix:
            filename = f"creative-workshop-{record.id}{suffix}"
        return StreamingResponse(
            BytesIO(response.content),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    raise HTTPException(status_code=400, detail="Unsupported image URL.")


@app.get("/api/history")
def history(db: Session = Depends(get_db)) -> list[dict[str, str | int]]:
    records = db.query(Generation).order_by(desc(Generation.id)).all()
    return [
        {
            "id": item.id,
            "topic": item.topic,
            "style": item.style,
            "idea": item.idea,
            "image_url": item.image_url,
            "prompt": item.prompt,
            "negative_prompt": item.negative_prompt,
            "created_at": item.created_at.isoformat(),
        }
        for item in records
    ]


