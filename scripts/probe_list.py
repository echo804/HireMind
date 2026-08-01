"""临时探测：验证 BUG-01 在当前后端的行为（知识库/简历列表）。"""
import uuid
import httpx

c = httpx.Client(timeout=30)
email = f"probe_{uuid.uuid4().hex[:6]}@test.com"
r = c.post("http://localhost:8000/api/auth/register",
           json={"email": email, "password": "pass1234", "nickname": "probe"})
token = r.json()["data"]["token"]
h = {"Authorization": f"Bearer {token}"}
print("register:", r.status_code)

r1 = c.get("http://localhost:8000/api/knowledge", headers=h)
print("kb list:", r1.status_code, r1.text[:160])

r2 = c.get("http://localhost:8000/api/resumes", headers=h)
print("resume list:", r2.status_code, r2.text[:160])
