import pytest
from finance_tracker.categories import CategoryType
from finance_tracker.database import DatabaseClient
from finance_tracker.models import Rule, Transaction

from tests.conftest import make_rule, make_transaction


class TestAdd:
    def test_add_and_retrieve(self, database: DatabaseClient):
        transaction = make_transaction()
        database.add(transaction)
        result = database.select_one(
            Transaction, Transaction.description == "CARD PAYMENT TO TESCO STORES"
        )
        assert result.amount == -50.00

    def test_add_if_new_returns_true_for_new(self, database: DatabaseClient):
        transaction = make_transaction()
        assert database.add_if_new(transaction) is True

    def test_add_if_new_returns_false_for_duplicate(self, database: DatabaseClient):
        transaction = make_transaction()
        database.add(transaction)
        duplicate = make_transaction()
        assert database.add_if_new(duplicate) is False

    def test_add_if_new_does_not_corrupt_session(self, database: DatabaseClient):
        database.add(make_transaction(description="First", transaction_hash="hash_1"))
        database.add_if_new(make_transaction(description="First", transaction_hash="hash_1"))
        database.add(make_transaction(description="Second", transaction_hash="hash_2"))
        assert database.count(Transaction) == 2


class TestSelectWhere:
    def test_filters_by_category(self, populated_database: DatabaseClient):
        groceries = populated_database.select_where(
            Transaction, Transaction.category == CategoryType.GROCERIES
        )
        assert len(groceries) == 2

    def test_filters_by_account(self, populated_database: DatabaseClient):
        results = populated_database.select_where(Transaction, Transaction.account == "Everyday")
        assert len(results) == 12

    def test_returns_empty_for_no_match(self, populated_database: DatabaseClient):
        results = populated_database.select_where(Transaction, Transaction.account == "Nonexistent")
        assert len(results) == 0


class TestSelectOne:
    def test_returns_single_result(self, populated_database: DatabaseClient):
        result = populated_database.select_one(
            Transaction, Transaction.description == "CARD PAYMENT TO DELIVEROO"
        )
        assert result.amount == -18.99

    def test_raises_for_no_match(self, populated_database: DatabaseClient):
        with pytest.raises(ValueError, match="No Transaction found"):
            populated_database.select_one(Transaction, Transaction.description == "NONEXISTENT")

    def test_raises_for_multiple(self, populated_database: DatabaseClient):
        with pytest.raises(ValueError, match="Multiple Transaction found"):
            populated_database.select_one(
                Transaction, Transaction.category == CategoryType.GROCERIES
            )


class TestSelectOneOrNone:
    def test_returns_none_for_no_match(self, populated_database: DatabaseClient):
        result = populated_database.select_one_or_none(
            Transaction, Transaction.description == "NONEXISTENT"
        )
        assert result is None


class TestClearTable:
    def test_removes_all_rows(self, populated_database: DatabaseClient):
        count = populated_database.clear_table(Transaction)
        assert count == 13
        assert populated_database.count(Transaction) == 0

    def test_does_not_affect_other_tables(self, database_with_rules: DatabaseClient):
        database_with_rules.clear_table(Transaction)
        assert database_with_rules.count(Rule) > 0


class TestRules:
    def test_add_and_retrieve_rule(self, database: DatabaseClient):
        rule = make_rule("TESCO", CategoryType.GROCERIES)
        database.add(rule)
        result = database.select_one(Rule, Rule.pattern == "TESCO")
        assert result.category == CategoryType.GROCERIES
        assert result.source == "manual"
