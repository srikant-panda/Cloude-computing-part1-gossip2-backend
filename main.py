import os
import uuid
import shutil
import subprocess
import asyncio
import logging
import time

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func, select, text, MetaData

from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from os import getenv
from slowapi import Limiter
from slowapi.util import get_remote_address   # To get the ip address of user.
from slowapi.middleware import SlowAPIASGIMiddleware   # limiter middleware
from slowapi.errors import RateLimitExceeded    # Ratelimitexpection

import submit

# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("job-system")

# ================= CONFIG =================

load_dotenv()

DATABASE_URL = str(getenv("DATABASE_URL"))
DEFAULT_SCHEMA_NAME = "cloude_computing"

metadata = MetaData(schema=DEFAULT_SCHEMA_NAME)

# ================= DATABASE =================

class Base(DeclarativeBase):
    metadata = metadata


class RequestModel(Base):
    __tablename__ = 'requests_sem_3'
    __table_args__ = {"schema": DEFAULT_SCHEMA_NAME}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    click: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"statement_cache_size": 0}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def getDb():
    async with AsyncSessionLocal() as session:
        yield session


# ================= RATE LIMITER =================

RATE_LIMIT = 3
RATE_WINDOW = 60  # seconds

rate_store = {}  # {email: [timestamps]}


def check_rate_limit(email: str):
    now = time.time()

    if email not in rate_store:
        rate_store[email] = []

    # remove old timestamps
    rate_store[email] = [
        t for t in rate_store[email] if now - t < RATE_WINDOW
    ]

    if len(rate_store[email]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before retrying."
        )

    rate_store[email].append(now)


# ================= JOB SYSTEM =================

jobs = {}


async def handle_job(job_id: str):
    job = jobs[job_id]
    process = job["process"]

    logger.info(f"[JOB {job_id}] STARTED | email={job['email']}")

    try:
        job["status"] = "grading"
        logger.info(f"[JOB {job_id}] GRADING")

        await asyncio.to_thread(process.wait)

        if process.returncode != 0:
            job["status"] = "failed"
            logger.error(f"[JOB {job_id}] FAILED (grading)")
            return

        job["status"] = "submitting"
        logger.info(f"[JOB {job_id}] SUBMITTING")

        result = await submit.submit(
            job["email"],
            job["token"],
            job["job_dir"],
            os.getcwd()
        )

        if not result.get("success"):
            job["status"] = "failed"
            job["result"] = result
            logger.error(f"[JOB {job_id}] FAILED → {result.get('error')}")
            return

        job["status"] = "done"
        job["result"] = result
        logger.info(f"[JOB {job_id}] SUCCESS")

    except Exception as e:
        job["status"] = "failed"
        job["result"] = {"error": str(e)}
        logger.exception(f"[JOB {job_id}] CRASHED")

    finally:
        shutil.rmtree(job["job_dir"], ignore_errors=True)
        logger.info(f"[JOB {job_id}] CLEANED")


# ================= API =================

class Info(BaseModel):
    email: EmailStr
    token: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 App started")
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DEFAULT_SCHEMA_NAME}"'))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.info("Database connection failde. Your data is not storing to database.")

    yield

    await engine.dispose()
    logger.info("🛑 App stopped")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
limiter=Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIASGIMiddleware)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request : Request,exec : RateLimitExceeded):
    raise HTTPException(
           status_code=429,
            detail="Too many requests. limit execeed. Try after 10 minutes"
    )

# ================= ROUTES =================

@app.post("/submit")
@limiter.limit("3/minutes")
async def submit_application(data: Info, db: AsyncSession = Depends(getDb)):
    logger.info(f"[REQUEST] {data.email}")

    # 🔥 RATE LIMIT CHECK
    check_rate_limit(data.email)

    job_id = str(uuid.uuid4())
    job_dir = f"/tmp/{job_id}"
    os.makedirs(job_dir, exist_ok=True)

    # DB tracking
    db_result = await db.execute(
        select(RequestModel).where(RequestModel.email == data.email)
    )
    user = db_result.scalar_one_or_none()

    if not user:
        db.add(RequestModel(email=data.email))
    else:
        user.click += 1

    await db.commit()

    process = subprocess.Popen(
        ['sh', 'run.sh', job_dir, os.getcwd()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    jobs[job_id] = {
        "process": process,
        "status": "running",
        "job_dir": job_dir,
        "email": data.email,
        "token": data.token
    }

    asyncio.create_task(handle_job(job_id))

    return {
        "job_id": job_id,
        "status": "running",
        "msg": "Submission started"
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get(job_id)

    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "status": job["status"],
        "result": job.get("result")
    }


@app.post("/cancel/{job_id}")
def cancel_job(job_id: str):
    job = jobs.get(job_id)

    if not job:
        raise HTTPException(404, "Job not found")

    process = job["process"]

    if process.poll() is None:
        process.kill()
        job["status"] = "killed"
        logger.warning(f"[JOB {job_id}] CANCELLED")

    shutil.rmtree(job["job_dir"], ignore_errors=True)

    return {"msg": "Job cancelled"}


@app.get("/health")
async def health():
    return {"status": "running"}