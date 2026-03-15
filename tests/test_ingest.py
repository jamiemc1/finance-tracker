from datetime import date
from pathlib import Path

from finance_tracker.categories import CategoryType
from finance_tracker.ingest import parse_santander_txt


class TestParseSantanderTxt:
    def test_parses_all_transactions(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        assert len(transactions) == 19

    def test_sets_account_name(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Current")
        assert all(t.account == "Current" for t in transactions)

    def test_parses_dates(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        first = transactions[0]
        assert first.transaction_date == date(2026, 2, 28)

    def test_parses_negative_amounts(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        outgoing = [t for t in transactions if "BRITISH GAS" in t.description]
        assert len(outgoing) == 1
        assert outgoing[0].amount == -85.00

    def test_parses_positive_amounts(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        incoming = [t for t in transactions if "TRANSFER FROM" in t.description]
        assert all(t.amount > 0 for t in incoming)

    def test_all_transactions_start_uncategorised(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        assert all(t.category == CategoryType.UNCATEGORISED for t in transactions)

    def test_each_transaction_has_unique_hash(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        hashes = [t.transaction_hash for t in transactions]
        assert len(hashes) == len(set(hashes))

    def test_preserves_full_description(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        gas_transaction = [t for t in transactions if "BRITISH GAS" in t.description][0]
        assert gas_transaction.description == "DIRECT DEBIT PAYMENT TO BRITISH GAS, MANDATE NO 0001"

    def test_skips_header_and_footer(self, sample_statement_path: Path):
        transactions = parse_santander_txt(sample_statement_path, "Everyday")
        descriptions = [t.description for t in transactions]
        assert not any("Arranged overdraft" in d for d in descriptions)
        assert not any("From:" in d for d in descriptions)
