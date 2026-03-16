from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TypeVar

from sqlalchemy import BinaryExpression
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from finance_tracker.seeds import build_seed_rules

DATA_DIR = Path.home() / ".finance-tracker"
DB_PATH = DATA_DIR / "finance.db"

T = TypeVar("T", bound=SQLModel)


class DatabaseClient:
    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    @contextmanager
    def create(cls, db_path: Path = DB_PATH):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        is_new_database = not db_path.exists()
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            client = cls(session)
            if is_new_database:
                for rule in build_seed_rules():
                    client.add(rule)
            yield client

    @classmethod
    @contextmanager
    def create_null(cls):
        engine = create_engine("sqlite://", echo=False)
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            yield cls(session)

    def add(self, obj: SQLModel) -> None:
        self._session.add(obj)
        self._session.flush()

    def add_if_new(self, obj: SQLModel) -> bool:
        """Add object if it doesn't violate a unique constraint. Returns True if inserted."""
        try:
            with self._session.begin_nested():
                self._session.add(obj)
                self._session.flush()
            return True
        except IntegrityError:
            return False

    def add_all(self, objects: Sequence[SQLModel]) -> None:
        self._session.add_all(objects)
        self._session.flush()

    def delete(self, obj: SQLModel) -> None:
        self._session.delete(obj)
        self._session.flush()

    def select_where(
        self,
        model: type[T],
        *where: BinaryExpression,
    ) -> Sequence[T]:
        statement = select(model)
        for condition in where:
            statement = statement.where(condition)
        return self._session.exec(statement).all()

    def select_one(self, model: type[T], *where: BinaryExpression) -> T:
        results = self.select_where(model, *where)
        if len(results) == 0:
            raise ValueError(f"No {model.__name__} found matching query")
        if len(results) > 1:
            raise ValueError(f"Multiple {model.__name__} found matching query, expected one")
        return results[0]

    def select_one_or_none(self, model: type[T], *where: BinaryExpression) -> T | None:
        results = self.select_where(model, *where)
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise ValueError(f"Multiple {model.__name__} found matching query, expected one")
        return results[0]

    def select_all(self, model: type[T]) -> Sequence[T]:
        return self.select_where(model)

    def count(self, model: type[T], *where: BinaryExpression) -> int:
        return len(self.select_where(model, *where))

    def clear_table(self, model: type[T]) -> int:
        rows = self.select_all(model)
        for row in rows:
            self._session.delete(row)
        self._session.flush()
        return len(rows)

    @staticmethod
    def purge() -> None:
        import shutil

        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR)
