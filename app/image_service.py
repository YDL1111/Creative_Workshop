import base64
import time
from datetime import datetime
from pathlib import Path

import httpx

from app.config import get_settings

MOCK_SVG_TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024' viewBox='0 0 1024 1024'>
<defs>
  <linearGradient id='bg' x1='0' x2='1' y1='0' y2='1'>
    <stop offset='0' stop-color='#f5efe3'/><stop offset='0.5' stop-color='#d6e3dc'/><stop offset='1' stop-color='#2f4858'/>
  </linearGradient>
  <filter id='grain'><feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/><feComponentTransfer><feFuncA type='table' tableValues='0 .12'/></feComponentTransfer></filter>
</defs>
<rect width='1024' height='1024' fill='url(#bg)'/>
<rect width='1024' height='1024' filter='url(#grain)' opacity='.35'/>
<path d='M116 700 C250 510 348 456 512 526 C678 598 769 492 908 328' fill='none' stroke='#17242b' stroke-width='28' stroke-linecap='round' opacity='.82'/>
<circle cx='310' cy='320' r='92' fill='#d94f30' opacity='.92'/>
<rect x='188' y='720' width='648' height='78' rx='8' fill='#17242b' opacity='.86'/>
<text x='512' y='768' text-anchor='middle' font-family='Georgia, serif' font-size='32' fill='#fff7e8'>Creative Workshop Mock Image</text>
</svg>"""

# PackyAPI gpt-image-2 documented sizes include: auto, 1024x1024,
# 1536x1024, 1024x1536, 1536x864, 3840x2160.
SIZE_BY_RATIO = {
    "1:1": "1024x1024",
    "3:4": "1024x1536",
    "2:3": "1024x1536",
    "4:3": "1536x1024",
    "9:16": "1024x1536",
    "16:9": "1536x864",
}



def _log_image_event(message: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n"
    Path("image_api.log").open("a", encoding="utf-8").write(line)

class ImageGenerationError(RuntimeError):
    pass


async def generate_image(prompt: str, negative_prompt: str, ratio: str = "1:1") -> tuple[str, str]:
    settings = get_settings()
    provider = settings.image_provider.lower().strip() or "mock"
    size = SIZE_BY_RATIO.get(ratio, "1024x1024")

    if provider == "mock":
        return _save_mock_image(), "mock"
    if provider == "openai_compatible":
        return await _generate_openai_compatible(prompt, negative_prompt, size), provider

    raise ImageGenerationError(f"Unsupported IMAGE_PROVIDER: {settings.image_provider}")


def _save_mock_image() -> str:
    output_dir = Path("app/static/generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"mock-{int(time.time() * 1000)}.svg"
    path = output_dir / filename
    path.write_text(MOCK_SVG_TEMPLATE, encoding="utf-8")
    return f"/static/generated/{filename}"


def _build_image_generation_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    if not cleaned.startswith(("http://", "https://")):
        raise ImageGenerationError(
            "IMAGE_API_BASE_URL must be a full URL, for example https://www.packyapi.com/v1. "
            "Do not set it to /v1/images/generations."
        )
    if cleaned.endswith("/images/generations"):
        return cleaned
    return f"{cleaned}/images/generations"


def _read_error_message(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = response.json()
            detail = data.get("error", data)
            if isinstance(detail, dict):
                return str(detail.get("message") or detail)
            return str(detail)
        except ValueError:
            pass
    text = response.text.strip()
    if "Bad gateway" in text or "Error code 502" in text:
        return "Image API gateway returned 502 Bad Gateway. Check IMAGE_API_BASE_URL or try again later."
    return text[:500] or f"Image API request failed with HTTP {response.status_code}."


async def _generate_openai_compatible(prompt: str, negative_prompt: str, size: str) -> str:
    settings = get_settings()
    if not settings.image_api_key or not settings.image_api_base_url:
        raise ImageGenerationError("IMAGE_API_KEY and IMAGE_API_BASE_URL are required.")

    final_prompt = f"{prompt}\n避免：{negative_prompt}" if negative_prompt else prompt
    payload = {
        "model": settings.image_model or "gpt-image-2",
        "prompt": final_prompt,
        "size": size,
    }
    headers = {
        "Authorization": f"Bearer {settings.image_api_key}",
        "Content-Type": "application/json",
    }

    url = _build_image_generation_url(settings.image_api_base_url)
    started = time.perf_counter()
    _log_image_event(f'request url={url} model={payload.get("model")} size={payload.get("size")}')
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(420.0, connect=30.0)) as client:
            response = await client.post(url, json=payload, headers=headers)
            _log_image_event(f'response status={response.status_code} elapsed={time.perf_counter() - started:.1f}s content_type={response.headers.get("content-type", "")} preview={response.text[:300]!r}')
    except httpx.RequestError as exc:
        _log_image_event(f'connection_error elapsed={time.perf_counter() - started:.1f}s error={exc}')
        raise ImageGenerationError(f"Image API connection failed: {exc}") from exc

    if response.status_code >= 400:
        raise ImageGenerationError(_read_error_message(response))

    try:
        data = response.json()
    except ValueError as exc:
        raise ImageGenerationError("Image API returned non-JSON response.") from exc
    if isinstance(data, dict):
        if data.get("url"):
            return data["url"]
        if data.get("b64_json"):
            return _save_base64_image(data["b64_json"])
        items = data.get("data") or data.get("images") or data.get("result") or []
        if isinstance(items, dict):
            items = [items]
        if items:
            item = items[0]
            if item.get("url"):
                return item["url"]
            if item.get("b64_json"):
                return _save_base64_image(item["b64_json"])

    summary = str(data)[:500]
    raise ImageGenerationError(f"Image API response did not include url or b64_json. Response preview: {summary}")


def _save_base64_image(raw: str) -> str:
    output_dir = Path("app/static/generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"image-{int(time.time() * 1000)}.png"
    path = output_dir / filename
    path.write_bytes(base64.b64decode(raw))
    return f"/static/generated/{filename}"



