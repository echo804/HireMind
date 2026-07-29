import json, os, logging
from pathlib import Path

logger = logging.getLogger(__name__)

SETTINGS_DIR = Path("./settings_data")
SETTINGS_DIR.mkdir(exist_ok=True)

DEFAULT_SETTINGS = {
    "provider": "bailian",
    "bailian_api_key": "",
    "bailian_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "bailian_model": "qwen3.5-flash",
    "deepseek_api_key": "",
    "deepseek_base_url": "https://api.deepseek.com",
    "deepseek_model": "deepseek-chat",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_model": "gpt-4o-mini",
}


def _file(user_id: str | None = None) -> Path:
    uid = user_id or "default"
    # 用 user_id 的前 8 位做目录分片，避免单目录文件过多
    return SETTINGS_DIR / f"{uid}.json"


def _load(user_id: str | None = None) -> dict:
    f = _file(user_id)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load settings for {user_id}: {e}")
    return {}


def _save(data: dict, user_id: str | None = None):
    _file(user_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_settings(user_id: str | None = None) -> dict:
    saved = _load(user_id)
    result = DEFAULT_SETTINGS.copy()
    result.update(saved)
    for key in ["bailian_api_key", "deepseek_api_key", "openai_api_key"]:
        if result.get(key):
            result[key] = result[key][:4] + "*" * (len(result[key]) - 8) + result[key][-4:]
    return result


def update_settings(data: dict, user_id: str | None = None) -> dict:
    saved = _load(user_id)
    for key in DEFAULT_SETTINGS:
        if key in data:
            val = data[key]
            # 跳过掩码值（含 *** 表示用户未修改）
            if "api_key" in key and val and "**" in val:
                continue
            saved[key] = val
    if not saved.get("bailian_api_key"):
        from app.config.settings import settings as s
        if s.AI_BAILIAN_API_KEY:
            saved["bailian_api_key"] = s.AI_BAILIAN_API_KEY
    if not saved.get("deepseek_api_key"):
        from app.config.settings import settings as s
        if s.DEEPSEEK_API_KEY:
            saved["deepseek_api_key"] = s.DEEPSEEK_API_KEY
    if not saved.get("openai_api_key"):
        from app.config.settings import settings as s
        if s.OPENAI_API_KEY:
            saved["openai_api_key"] = s.OPENAI_API_KEY
    _save(saved, user_id)
    return get_settings(user_id)


def get_active_config(user_id: str | None = None) -> dict:
    """Get the active LLM config for the given user (or default)"""
    saved = _load(user_id)
    provider = saved.get("provider", "bailian")
    from app.config.settings import settings as s
    if provider == "bailian" and (saved.get("bailian_api_key") or s.AI_BAILIAN_API_KEY):
        return {
            "api_key": saved.get("bailian_api_key") or s.AI_BAILIAN_API_KEY,
            "base_url": saved.get("bailian_base_url") or s.AI_BAILIAN_BASE_URL,
            "model": saved.get("bailian_model") or s.AI_DEFAULT_MODEL,
        }
    if provider == "deepseek" and (saved.get("deepseek_api_key") or s.DEEPSEEK_API_KEY):
        return {
            "api_key": saved.get("deepseek_api_key") or s.DEEPSEEK_API_KEY,
            "base_url": saved.get("deepseek_base_url") or s.DEEPSEEK_BASE_URL,
            "model": saved.get("deepseek_model") or "deepseek-chat",
        }
    if provider == "openai" and (saved.get("openai_api_key") or s.OPENAI_API_KEY):
        return {
            "api_key": saved.get("openai_api_key") or s.OPENAI_API_KEY,
            "base_url": saved.get("openai_base_url") or s.OPENAI_BASE_URL,
            "model": saved.get("openai_model") or "gpt-4o-mini",
        }
    # Fallback to .env
    api_key = s.AI_BAILIAN_API_KEY or s.DEEPSEEK_API_KEY or s.OPENAI_API_KEY
    base_url = s.AI_BAILIAN_BASE_URL if s.AI_BAILIAN_API_KEY else s.DEEPSEEK_BASE_URL if s.DEEPSEEK_API_KEY else s.OPENAI_BASE_URL
    model = s.AI_DEFAULT_MODEL
    return {"api_key": api_key or "", "base_url": base_url or "", "model": model or ""}
