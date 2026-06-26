from sqlalchemy import create_engine
from sqlmodel import Session
from app.config.settings import Settings

settings = Settings()
engine = create_engine(settings.database_url, echo=settings.debug)

def get_session() -> Session:
    return Session(engine)