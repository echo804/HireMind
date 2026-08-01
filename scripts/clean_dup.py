import asyncio
from sqlalchemy import text
from app.infrastructure.database import engine

async def main():
    async with engine.begin() as conn:
        result = await conn.execute(text("DELETE FROM resumes WHERE status = 'FAILED' AND summary = 'Duplicate resume'"))
        print(f"Deleted {result.rowcount} duplicate records")
asyncio.run(main())
