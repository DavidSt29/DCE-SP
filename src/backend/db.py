import time
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config
from models import Base

logger = logging.getLogger(__name__)

# Configure SQLAlchemy Engine based on database dialect
if Config.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        Config.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # Production PostgreSQL connection pool with connection health pre-ping
    engine = create_engine(
        Config.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# Thread-safe database session management (scoped_session)
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
ScopedSession = scoped_session(SessionFactory)

@contextmanager
def get_db_session():
    """
    Context manager for database transaction lifecycle.
    Automatically commits on success, rolls back on exception, and ensures session closure.
    """
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db(retries: int = 15, delay: int = 2) -> bool:
    """
    Initialize database connection with a retry loop.
    Ensures backend waits until PostgreSQL container is fully ready and creates schema tables.
    """
    logger.info("Initializing database connection...")
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully.")
            
            # Create tables defined in models if they do not exist
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified / created successfully.")
            return True
        except Exception as e:
            logger.warning(
                f"Database connection attempt {attempt}/{retries} failed: {e}. Retrying in {delay}s..."
            )
            time.sleep(delay)

    logger.error("Could not connect to database after maximum retries.")
    raise RuntimeError("Failed to connect to relational database.")
