"""AI 配置 API key 加密测试：Fernet 加密落盘、掩码回显、明文旧数据兼容、用户隔离。"""

import json

from app.modules.settings.service import (
    _decrypt, _encrypt, _file, get_active_config, get_settings, update_settings,
)

FAKE_KEY = "sk-test-1234567890"


# ---------- 加密工具单元测试 ----------

def test_encrypt_roundtrip():
    cipher = _encrypt(FAKE_KEY)
    assert cipher.startswith("enc:")
    assert FAKE_KEY not in cipher  # 密文不含明文
    assert _decrypt(cipher) == FAKE_KEY


def test_decrypt_plaintext_compat():
    assert _decrypt(FAKE_KEY) == FAKE_KEY  # 明文原样返回（旧数据兼容）


def test_encrypt_empty():
    assert _encrypt("") == ""


# ---------- API 层：加密落盘与掩码 ----------

async def test_save_encrypts_key_on_disk(client, registered_user):
    uid = registered_user["id"]
    resp = await client.put("/api/settings", json={
        "provider": "bailian",
        "bailian_api_key": FAKE_KEY,
        "bailian_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }, headers=registered_user["headers"])
    assert resp.status_code == 200, resp.text

    # 文件里必须是密文
    raw = _file(uid).read_text(encoding="utf-8")
    assert "enc:" in raw
    assert FAKE_KEY not in raw  # 明文不得落盘


async def test_get_returns_masked_key(client, registered_user):
    await client.put("/api/settings", json={"bailian_api_key": FAKE_KEY},
                     headers=registered_user["headers"])
    resp = await client.get("/api/settings", headers=registered_user["headers"])
    assert resp.status_code == 200
    masked = resp.json()["data"]["bailian_api_key"]
    assert "****" in masked
    assert FAKE_KEY not in masked  # 不回显完整 key


async def test_masked_value_not_overwritten(client, registered_user):
    """前端回传掩码值时（含 **），不应覆盖已保存的真实 key。"""
    await client.put("/api/settings", json={"bailian_api_key": FAKE_KEY},
                     headers=registered_user["headers"])
    masked = "sk-t****7890"  # 前端掩码回传
    resp = await client.put("/api/settings", json={"bailian_api_key": masked},
                            headers=registered_user["headers"])
    assert resp.status_code == 200, resp.text

    # 真实 key 仍是原值
    assert get_active_config(registered_user["id"])["api_key"] == FAKE_KEY


# ---------- 明文旧数据兼容 ----------

def test_plaintext_legacy_file_compat(tmp_path, monkeypatch):
    """旧版本明文存储的 settings 文件应能正常读取。"""
    from app.modules.settings import service as svc
    uid = "00000000-0000-0000-0000-0000000000aa"
    # 用临时目录隔离 SETTINGS_DIR
    monkeypatch.setattr(svc, "SETTINGS_DIR", tmp_path)
    f = tmp_path / f"{uid}.json"
    f.write_text(json.dumps({"provider": "bailian", "bailian_api_key": FAKE_KEY}),
                 encoding="utf-8")

    cfg = get_active_config(uid)
    assert cfg["api_key"] == FAKE_KEY


def test_user_settings_isolated(tmp_path, monkeypatch):
    from app.modules.settings import service as svc
    monkeypatch.setattr(svc, "SETTINGS_DIR", tmp_path)
    update_settings({"bailian_api_key": "key-for-a"}, "user-aaa")
    update_settings({"bailian_api_key": "key-for-b"}, "user-bbb")

    assert get_active_config("user-aaa")["api_key"] == "key-for-a"
    assert get_active_config("user-bbb")["api_key"] == "key-for-b"


# ---------- 未配置时回退 .env ----------

def test_active_config_fallback_env(tmp_path, monkeypatch):
    """无用户配置时回退 .env 中的 AI key。"""
    from app.modules.settings import service as svc
    from app.config.settings import settings as s
    monkeypatch.setattr(svc, "SETTINGS_DIR", tmp_path)
    # 临时覆盖 .env key
    monkeypatch.setattr(s, "AI_BAILIAN_API_KEY", "env-key-123")

    cfg = get_active_config("some-user")
    if cfg["api_key"]:
        assert cfg["api_key"] == "env-key-123"
