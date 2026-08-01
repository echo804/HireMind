"""探测 f18f9bb6 的 deepseek 配置是否可用（key + 模型 + 流式）。"""
import httpx

from app.modules.settings.service import get_active_config

cfg = get_active_config("f18f9bb6-45ea-41a5-9904-97e41245cdf3")
print("provider cfg:", cfg["base_url"], "model=", cfg["model"], "key_prefix=", cfg["api_key"][:8])

c = httpx.Client(timeout=60)
# 1. 普通调用
try:
    r = c.post(f"{cfg['base_url']}/chat/completions",
               headers={"Authorization": f"Bearer {cfg['api_key']}"},
               json={"model": cfg["model"],
                     "messages": [{"role": "user", "content": "你好，请回复OK"}],
                     "max_tokens": 20})
    print("普通调用:", r.status_code, r.text[:150])
except Exception as e:
    print("普通调用异常:", type(e).__name__, str(e)[:150])

# 2. 流式调用（模拟 generate_question_stream 的 astream）
try:
    with c.stream("POST", f"{cfg['base_url']}/chat/completions",
                  headers={"Authorization": f"Bearer {cfg['api_key']}"},
                  json={"model": cfg["model"],
                        "messages": [{"role": "user", "content": "你好，请流式回复OK"}],
                        "max_tokens": 20, "stream": True}) as resp:
        print("流式调用:", resp.status_code)
        chunks = 0
        for line in resp.iter_lines():
            if line.startswith("data:") and line != "data: [DONE]":
                chunks += 1
        print("流式 chunk 数:", chunks)
except Exception as e:
    print("流式调用异常:", type(e).__name__, str(e)[:150])
