"""Database setup using SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

database_url = make_url(settings.DATABASE_URL)
if database_url.drivername == "postgres":
    database_url = database_url.set(drivername="postgresql")

connect_args = {"check_same_thread": False} if database_url.get_backend_name() == "sqlite" else {}
if database_url.get_backend_name() == "postgresql":
    query = dict(database_url.query)
    query["sslmode"] = "require"
    database_url = database_url.set(query=query)

engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_default_user():
    """Create a default admin user for first-time login."""
    from models import User
    from utils.security import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.DEFAULT_USERNAME).first()
        if existing:
            return

        user = User(
            email=settings.DEFAULT_EMAIL,
            username=settings.DEFAULT_USERNAME,
            hashed_password=hash_password(settings.DEFAULT_PASSWORD),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        print(f"Default user created: username={settings.DEFAULT_USERNAME} password={settings.DEFAULT_PASSWORD}")
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from models import (
        User,
        YouTubeChannel,
        Script,
        GeneratedVideo,
        UploadHistory,
        AutomationSchedule,
        Setting,
        ActivityLog,
    )
    Base.metadata.create_all(bind=engine)
    create_default_user()
