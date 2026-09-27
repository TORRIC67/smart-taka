"""Smart Taka backend entry point.
Run from the backend/ folder:   uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers all tables)
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.payments.service import reconcile_pending
from app.routers import admin, auth, billing, complaints, payments, routes, sensors

log = logging.getLogger("smarttaka")


def _reconcile_once() -> None:
    with SessionLocal() as db:
        reconcile_pending(db, payments.get_provider())


async def _reconcile_loop() -> None:
    """Safety net for lost webhooks: re-check pending payments every 90 seconds."""
    while True:
        await asyncio.sleep(90)
        try:
            await asyncio.to_thread(_reconcile_once)
        except Exception:
            log.exception("Payment reconcile failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Development convenience: create tables if missing. For production use Alembic migrations.
    Base.metadata.create_all(engine)
    if settings.PAYMENT_PROVIDER == "mock":
        log.warning("PAYMENT_PROVIDER=mock: payments are FAKE. Development only, never in production.")
    use_reconcile = settings.PAYMENT_PROVIDER == "mock" or settings.HARAKAPAY_API_KEY
    task = asyncio.create_task(_reconcile_loop()) if use_reconcile else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Smart Taka", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(complaints.router)
app.include_router(billing.router)
app.include_router(sensors.router)
app.include_router(routes.admin_router)
app.include_router(routes.driver_router)


@app.get("/health")
def health():
    return {"status": "ok"}
