from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# pool_pre_ping: a held connection is tested with a lightweight "is this
# still alive" query before being reused, and transparently replaced if
# not. Matters most on a free-tier serverless Postgres like Neon, whose
# compute can suspend after a few minutes idle and drop connections our
# pool was still holding open - without this, the first request after a
# resume would fail on a stale connection instead of just reconnecting.
# Harmless (and cheap) for SQLite too, so left unconditional.
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)

if is_sqlite:
    # SQLite ignores foreign key constraints unless enabled per connection.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
