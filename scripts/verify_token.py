"""验证 f18f9bb6 身份 token：签发 JWT 并调用受保护接口确认归属。"""
import uuid

import httpx

from app.common.auth import create_access_token

USER_ID = "f18f9bb6-45ea-41a5-9904-97e41245cdf3"
RESUME_ID = "214b3bc9-da5b-45f6-8eaa-7cfe422f9671"

token = create_access_token(uuid.UUID(USER_ID))
h = {"Authorization": f"Bearer {token}"}
print("token 签发:", token[:20], "...")

c = httpx.Client(timeout=30)
r = c.get("http://localhost:8000/api/resumes", headers=h)
print("GET /api/resumes:", r.status_code)
if r.status_code == 200:
    items = r.json()["data"]
    print("简历数:", len(items))
    mine = [x for x in items if x["id"] == RESUME_ID]
    print("含当前简历 214b3bc9:", bool(mine), mine[0]["name"] if mine else "")

r2 = c.get(f"http://localhost:8000/api/resumes/{RESUME_ID}", headers=h)
print("GET /api/resumes/214b3bc9:", r2.status_code,
      r2.json()["data"]["position"] if r2.status_code == 200 else r2.text[:100])
