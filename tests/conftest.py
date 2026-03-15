from datetime import date
from pathlib import Path

import pytest
from finance_tracker.categories import CategoryType
from finance_tracker.database import DatabaseClient
from finance_tracker.models import Rule, Transaction

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def make_transaction(
    description: str = "CARD PAYMENT TO TESCO STORES",
    amount: float = -50.00,
    balance: float = 950.00,
    account: str = "Everyday",
    category: CategoryType = CategoryType.UNCATEGORISED,
    transaction_date: date | None = None,
    transaction_hash: str | None = None,
) -> Transaction:
    """Factory for creating test transactions with sensible defaults."""
    if transaction_date is None:
        transaction_date = date(2026, 2, 15)
    if transaction_hash is None:
        transaction_hash = f"{transaction_date}|{description}|{amount}|{balance}"
    return Transaction(
        transaction_date=transaction_date,
        description=description,
        amount=amount,
        balance=balance,
        account=account,
        category=category,
        transaction_hash=transaction_hash,
    )


def make_rule(
    pattern: str = "TESCO",
    category: CategoryType = CategoryType.GROCERIES,
    source: str = "manual",
) -> Rule:
    """Factory for creating test rules with sensible defaults."""
    return Rule(pattern=pattern, category=category, source=source)


@pytest.fixture
def sample_statement_path() -> Path:
    return FIXTURES_DIR / "sample_statement.txt"


@pytest.fixture
def database():
    with DatabaseClient.create_null() as db:
        yield db


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """A representative set of transactions spanning categories and dates."""
    return [
        make_transaction(
            description="TRANSFER FROM JAMIE LUKE MCMILLAN",
            amount=2500.00,
            balance=3200.50,
            transaction_date=date(2026, 2, 28),
            category=CategoryType.INCOME,
        ),
        make_transaction(
            description="DIRECT DEBIT PAYMENT TO BRITISH GAS",
            amount=-85.00,
            balance=700.50,
            transaction_date=date(2026, 2, 27),
            category=CategoryType.UTILITIES,
        ),
        make_transaction(
            description="CARD PAYMENT TO TESCO STORES 2345",
            amount=-67.43,
            balance=785.50,
            transaction_date=date(2026, 2, 25),
            category=CategoryType.GROCERIES,
        ),
        make_transaction(
            description="CARD PAYMENT TO DELIVEROO",
            amount=-18.99,
            balance=852.93,
            transaction_date=date(2026, 2, 22),
            category=CategoryType.EATING_OUT,
        ),
        make_transaction(
            description="DIRECT DEBIT PAYMENT TO NETFLIX.COM",
            amount=-15.99,
            balance=871.92,
            transaction_date=date(2026, 2, 20),
            category=CategoryType.SUBSCRIPTIONS,
        ),
        make_transaction(
            description="CARD PAYMENT TO SHELL PETROL STN",
            amount=-55.00,
            balance=887.91,
            transaction_date=date(2026, 2, 18),
            category=CategoryType.TRANSPORT,
        ),
        make_transaction(
            description="CARD PAYMENT TO SAINSBURYS S/MKTS",
            amount=-92.17,
            balance=942.91,
            transaction_date=date(2026, 2, 15),
            category=CategoryType.GROCERIES,
        ),
        make_transaction(
            description="DIRECT DEBIT PAYMENT TO AVIVA INSURANCE",
            amount=-45.50,
            balance=1067.08,
            transaction_date=date(2026, 2, 10),
            category=CategoryType.INSURANCE,
        ),
        make_transaction(
            description="CARD PAYMENT TO AMAZON.CO.UK",
            amount=-29.99,
            balance=1112.58,
            transaction_date=date(2026, 2, 5),
            category=CategoryType.SHOPPING,
        ),
        make_transaction(
            description="STANDING ORDER TO VANGUARD ISA",
            amount=-200.00,
            balance=-938.29,
            transaction_date=date(2026, 1, 15),
            category=CategoryType.SAVINGS_INVESTMENTS,
        ),
        make_transaction(
            description="CARD PAYMENT TO BOOKING.COM",
            amount=-350.00,
            balance=-1288.29,
            transaction_date=date(2026, 1, 20),
            category=CategoryType.HOLIDAYS_TRAVEL,
        ),
    ]


@pytest.fixture
def sample_rules() -> list[Rule]:
    """A representative set of categorisation rules."""
    return [
        make_rule("TESCO", CategoryType.GROCERIES),
        make_rule("SAINSBURYS", CategoryType.GROCERIES),
        make_rule("ALDI", CategoryType.GROCERIES),
        make_rule("BRITISH GAS", CategoryType.UTILITIES),
        make_rule("DELIVEROO", CategoryType.EATING_OUT),
        make_rule("NETFLIX", CategoryType.SUBSCRIPTIONS),
        make_rule("SHELL PETROL", CategoryType.TRANSPORT),
        make_rule("AVIVA INSURANCE", CategoryType.INSURANCE),
        make_rule("AMAZON", CategoryType.SHOPPING),
        make_rule("BOOKING.COM", CategoryType.HOLIDAYS_TRAVEL),
        make_rule("VANGUARD ISA", CategoryType.SAVINGS_INVESTMENTS),
    ]


@pytest.fixture
def populated_database(
    database: DatabaseClient, sample_transactions: list[Transaction]
) -> DatabaseClient:
    """Database pre-loaded with sample categorised transactions."""
    for transaction in sample_transactions:
        database.add(transaction)
    return database


@pytest.fixture
def database_with_rules(
    populated_database: DatabaseClient, sample_rules: list[Rule]
) -> DatabaseClient:
    """Database pre-loaded with both transactions and rules."""
    for rule in sample_rules:
        populated_database.add(rule)
    return populated_database
