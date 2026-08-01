"""创建 hiremind_test 测试数据库（连接 WSL PostgreSQL）。用法: python scripts/create_test_db.py"""
import asyncio
import os
import sys

import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    # 从 .env 读取数据库密码，避免硬编码
    pg_password = ""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            if line.startswith("POSTGRES_PASSWORD="):
                pg_password = line.split("=", 1)[1].strip()
    pg_password = os.environ.get("PGPASS") or pg_password

    conn = await asyncpg.connect(
        host="localhost", port=5432, user="postgres",
        password=pg_password, database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname='hiremind_test'")
        if not exists:
            await conn.execute("CREATE DATABASE hiremind_test")
            print("hiremind_test CREATED")
        else:
            print("hiremind_test EXISTS")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
