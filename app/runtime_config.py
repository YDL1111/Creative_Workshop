import os
from pathlib import Path

from app.config import get_settings
from app.schemas import RuntimeConfigResponse, RuntimeConfigUpdate

CONFIG_KEYS = {
    "IMAGE_PROVIDER",
    "IMAGE_API_KEY",
    "IMAGE_API_BASE_URL",
    "IMAGE_MODEL",
    "LLM_API_KEY",
    "LLM_API_BASE_URL",
    "LLM_MODEL",
}


def _env_path() -> Path:
    configured = os.getenv("APP_ENV_FILE", ".env")
    return Path(configured)


def _key_hint(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def read_runtime_config() -> RuntimeConfigResponse:
    settings = get_settings()
    return RuntimeConfigResponse(
        image_provider=settings.image_provider,
        image_api_base_url=settings.image_api_base_url,
        image_model=settings.image_model,
        image_api_key_set=bool(settings.image_api_key),
        image_api_key_hint=_key_hint(settings.image_api_key),
        llm_api_base_url=settings.llm_api_base_url,
        llm_model=settings.llm_model,
        llm_api_key_set=bool(settings.llm_api_key),
        llm_api_key_hint=_key_hint(settings.llm_api_key),
    )


def save_runtime_config(payload: RuntimeConfigUpdate) -> RuntimeConfigResponse:
    current = get_settings()
    values = {
        "IMAGE_PROVIDER": payload.image_provider.strip() or "mock",
        "IMAGE_API_BASE_URL": payload.image_api_base_url.strip(),
        "IMAGE_MODEL": payload.image_model.strip(),
        "LLM_API_BASE_URL": payload.llm_api_base_url.strip(),
        "LLM_MODEL": payload.llm_model.strip(),
        "IMAGE_API_KEY": payload.image_api_key.strip() or current.image_api_key,
        "LLM_API_KEY": payload.llm_api_key.strip() or current.llm_api_key,
    }

    path = _env_path()
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    updated: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            updated.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in CONFIG_KEYS:
            updated.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            updated.append(line)

    if updated and updated[-1].strip():
        updated.append("")
    for key in ("IMAGE_PROVIDER", "IMAGE_API_KEY", "IMAGE_API_BASE_URL", "IMAGE_MODEL", "LLM_API_KEY", "LLM_API_BASE_URL", "LLM_MODEL"):
        if key not in seen:
            updated.append(f"{key}={values[key]}")

    path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    for key, value in values.items():
        os.environ[key] = value
    return read_runtime_config()
