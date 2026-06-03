import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM
    llm_api_key: str = "sk-xxx"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "sqlite+aiosqlite:///./study_agent.db"

    # Chroma
    chroma_persist_dir: str = "./chroma_data"

    # Uploads
    upload_dir: str = "./uploads"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


# ─── Runtime overrides (set via API, persisted to JSON file) ───

_RUNTIME_CONFIG_FILE = Path(__file__).parent.parent / ".runtime_config.json"


def _load_runtime() -> dict:
    try:
        if _RUNTIME_CONFIG_FILE.exists():
            return json.loads(_RUNTIME_CONFIG_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_runtime(data: dict) -> None:
    _RUNTIME_CONFIG_FILE.write_text(json.dumps(data, indent=2))


def get_llm_api_key() -> str:
    return _load_runtime().get("llm_api_key") or settings.llm_api_key


def get_llm_base_url() -> str:
    return _load_runtime().get("llm_base_url") or settings.llm_base_url


def get_llm_model() -> str:
    return _load_runtime().get("llm_model") or settings.llm_model


def get_embedding_model() -> str:
    return _load_runtime().get("embedding_model") or settings.embedding_model


def set_runtime_settings(data: dict) -> dict:
    current = _load_runtime()
    for key in ("llm_api_key", "llm_base_url", "llm_model"):
        if key in data and data[key]:
            val = data[key]
            # Reject masked keys (from frontend pre-fill)
            if key == "llm_api_key" and "***" in val:
                continue
            current[key] = val
    _save_runtime(current)
    # Reset cached clients
    from app.services.llm import reset_clients
    from app.services.embedding import reset_embedding_client
    reset_clients()
    reset_embedding_client()
    return current


def get_current_settings() -> dict:
    runtime = _load_runtime()
    has_key = bool(runtime.get("llm_api_key"))
    return {
        # Return empty string when masked — frontend must re-enter
        "llm_api_key": "",
        "llm_api_key_configured": has_key,
        "llm_base_url": get_llm_base_url(),
        "llm_model": get_llm_model(),
        "has_runtime_config": bool(runtime),
    }


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]
