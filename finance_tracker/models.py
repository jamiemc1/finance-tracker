from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel

from finance_tracker.categories import CategoryType


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BaseMixin(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utc_now)


class Transaction(BaseMixin, table=True):
    transaction_date: date
    description: str
    amount: float
    balance: float
    account: str
    category: CategoryType = Field(default=CategoryType.UNCATEGORISED)
    transaction_hash: str = Field(unique=True, index=True)


class Rule(BaseMixin, table=True):
    pattern: str = Field(unique=True)
    category: CategoryType
    source: str = Field(default="manual")
