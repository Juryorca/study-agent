from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_current_settings, set_runtime_settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""


@router.get("")
async def get_settings():
    """Get current LLM settings (API key masked)."""
    return get_current_settings()


@router.post("")
async def update_settings(data: SettingsUpdate):
    """Update LLM settings at runtime. Only provided (non-empty) fields are updated."""
    updated = set_runtime_settings(data.model_dump(exclude_none=True))
    return {
        "message": "设置已更新，已重置 LLM 客户端",
        "updated": {
            "llm_base_url": updated.get("llm_base_url", ""),
            "llm_model": updated.get("llm_model", ""),
            # Don't return full API key
            "llm_api_key": (updated.get("llm_api_key", "")[:4] + "***") if updated.get("llm_api_key") else "",
        },
    }
