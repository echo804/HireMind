"""FastAPI App Entry"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.common.exception.handlers import register_exception_handlers
from app.common.model.base import Base
from app.infrastructure.database import engine
from app.infrastructure.redis import close_redis, init_redis
from app.modules.auth.router import router as auth_router
from app.modules.resume.router import router as resume_router
from app.modules.interview.router import router as interview_router
from app.modules.settings.router import router as settings_router
from app.modules.schedule.router import router as schedule_router
from app.modules.knowledgebase.router import router as knowledge_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    yield
    await close_redis()


app = FastAPI(title="HireMind", description="AI Interview Platform API", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173","http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(interview_router)
app.include_router(settings_router)
app.include_router(schedule_router)
app.include_router(knowledge_router)

app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
