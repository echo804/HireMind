import json, os, logging, base64
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

SETTINGS_DIR = Path("./settings_data")
SETTINGS_DIR.mkdir(exist_ok=True)

# 从 ENCRYPTION_KEY 派生 Fernet key（Fernet 要求 32 字节 urlsafe-base64）
def _get_fernet() -> Fernet:
    from app.config.settings import settings as s
    raw_key = s.ENCRYPTION_KEY
    # 确保 key 是 32 字节，不足则填充，超出则截断
    key_bytes = raw_key.encode("utf-8").ljust(32, b'\x00')[:32]
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def _encrypt(value: str) -> str:
    """加密敏感值，返回 'enc:' 前缀的密文"""
    if not value:
        return value
    try:
        f = _get_fernet()
        return "enc:" + f.encrypt(value.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return value  # 失败时返回明文（降级）


def _decrypt(value: str) -> str:
    """解密敏感值，兼容明文和 'enc:' 前缀密文"""
    if not value:
        return value
    if not value.startswith("enc:"):
        return value  # 已是明文（向后兼容旧数据）
    try:
        f = _get_fernet()
        return f.decrypt(value[4:].encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return value  # 解密失败返回原值

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
            data = json.loads(f.read_text(encoding="utf-8"))
            # 解密 api_key 字段（兼容明文旧数据）
            for key in ["bailian_api_key", "deepseek_api_key", "openai_api_key"]:
                if data.get(key):
                    data[key] = _decrypt(data[key])
            return data
        except Exception as e:
            logger.error(f"Failed to load settings for {user_id}: {e}")
    return {}


def _save(data: dict, user_id: str | None = None):
    # 加密 api_key 字段后再保存
    to_save = data.copy()
    for key in ["bailian_api_key", "deepseek_api_key", "openai_api_key"]:
        if to_save.get(key):
            to_save[key] = _encrypt(to_save[key])
    _file(user_id).write_text(json.dumps(to_save, ensure_ascii=False, indent=2), encoding="utf-8")


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
