from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class DatabaseConfig:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._is_sqlite = database_url.startswith("sqlite")
        connect_args = {"check_same_thread": False} if self._is_sqlite else {}
        self.engine: Engine = create_engine(database_url, connect_args=connect_args)
        self.SessionLocal: sessionmaker[Session] = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    @property
    def is_sqlite(self) -> bool:
        return self._is_sqlite

    def get_session(self) -> Session:
        return self.SessionLocal()
