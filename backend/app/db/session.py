from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_url = settings.DATABASE_URL
# Render (and many hosts) hand out plain "postgresql://" URLs. SQLAlchemy then
# defaults to the psycopg2 driver, which isn't installed here (we install
# psycopg 3 via "psycopg[binary]"). Force the psycopg3 driver explicitly so
# this works regardless of which URL format the database provider gives us.
if _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+psycopg://", 1)

# SQLite needs this flag because FastAPI uses several threads; PostgreSQL does not.
_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
if _url.startswith("postgresql+psycopg://"):
    # Fail fast instead of hanging silently if the database is unreachable
    # (e.g. wrong region, network issue) - without this, a bad connection
    # can hang until the host's deploy health check times out.
    _args["connect_timeout"] = 10
engine = create_engine(_url, connect_args=_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
