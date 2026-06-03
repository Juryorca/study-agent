import asyncio
import os
import signal
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models.base import Base

MAX_MEMORY_MB = 1024  # 1GB — kill process if exceeded


async def _memory_watchdog():
    proc = psutil.Process()
    while True:
        mem_mb = proc.memory_info().rss / (1024 * 1024)
        if mem_mb > MAX_MEMORY_MB:
            os.kill(os.getpid(), signal.SIGKILL)
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight migrations for dev
        for sql in [
            "ALTER TABLE knowledge_points ADD COLUMN mastery VARCHAR(20) NOT NULL DEFAULT 'unlearned'",
            "ALTER TABLE knowledge_points ADD COLUMN chapter VARCHAR(200) NOT NULL DEFAULT ''",
        ]:
            try:
                await conn.run_sync(lambda c: c.exec_driver_sql(sql))
            except Exception:
                pass
    watchdog_task = asyncio.create_task(_memory_watchdog())
    yield
    watchdog_task.cancel()
    await engine.dispose()


app = FastAPI(
    title="Study Agent API",
    description="基于 RAG 与 Tool Calling 的个性化课程复习智能体",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "study-agent"}


# Import routers (imports trigger tool registrations)
from app.routers import courses, documents, knowledge, questions, answers, analysis, agent_chat, chat_sessions, exams, settings  # noqa: E402

app.include_router(courses.router, prefix="/api/courses", tags=["课程管理"])
app.include_router(documents.router, prefix="/api/documents", tags=["资料管理"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识点与提纲"])
app.include_router(questions.router, prefix="/api/questions", tags=["题目管理"])
app.include_router(answers.router, prefix="/api/answers", tags=["答题评估"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["薄弱点分析"])
app.include_router(agent_chat.router, prefix="/api/agent", tags=["Agent 对话"])
app.include_router(chat_sessions.router, prefix="/api/agent", tags=["会话管理"])
app.include_router(exams.router, prefix="/api/exams", tags=["试卷管理"])
app.include_router(settings.router, prefix="/api/settings", tags=["系统设置"])


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
