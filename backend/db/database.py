from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./onw.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    # Add role_revealed to player_roles if missing (e.g. existing DBs)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT 1 FROM pragma_table_info('player_roles') WHERE name='role_revealed'"
        ))
        if result.scalar() is None:
            conn.execute(text(
                "ALTER TABLE player_roles ADD COLUMN role_revealed BOOLEAN DEFAULT 0"
            ))
            conn.commit()
