from pathlib import Path

import pytest
from finance_tracker.database import DatabaseClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_statement_path() -> Path:
    return FIXTURES_DIR / "sample_statement.txt"


@pytest.fixture
def database():
    with DatabaseClient.create_null() as db:
        yield db
