from finance_tracker.categories import CategoryType
from finance_tracker.database import DatabaseClient
from finance_tracker.models import Rule
from finance_tracker.rules import _extract_pattern, apply_rules, create_rule_from_description

from tests.conftest import make_rule, make_transaction


class TestApplyRules:
    def test_matches_keyword_in_description(self, database: DatabaseClient):
        database.add(make_rule("TESCO", CategoryType.GROCERIES))
        transactions = [make_transaction(description="CARD PAYMENT TO TESCO STORES 2345")]
        matched, unmatched = apply_rules(database, transactions)
        assert matched == 1
        assert unmatched == 0
        assert transactions[0].category == CategoryType.GROCERIES

    def test_case_insensitive_matching(self, database: DatabaseClient):
        database.add(make_rule("tesco", CategoryType.GROCERIES))
        transactions = [make_transaction(description="CARD PAYMENT TO TESCO STORES")]
        matched, _ = apply_rules(database, transactions)
        assert matched == 1

    def test_leaves_unmatched_as_uncategorised(self, database: DatabaseClient):
        database.add(make_rule("TESCO", CategoryType.GROCERIES))
        transactions = [make_transaction(description="CARD PAYMENT TO UNKNOWN SHOP")]
        _, unmatched = apply_rules(database, transactions)
        assert unmatched == 1
        assert transactions[0].category == CategoryType.UNCATEGORISED

    def test_skips_already_categorised(self, database: DatabaseClient):
        database.add(make_rule("TESCO", CategoryType.GROCERIES))
        transactions = [
            make_transaction(
                description="CARD PAYMENT TO TESCO",
                category=CategoryType.SHOPPING,
            )
        ]
        matched, _ = apply_rules(database, transactions)
        assert matched == 1
        assert transactions[0].category == CategoryType.SHOPPING

    def test_multiple_rules(self, database: DatabaseClient):
        database.add(make_rule("TESCO", CategoryType.GROCERIES))
        database.add(make_rule("NETFLIX", CategoryType.SUBSCRIPTIONS))
        transactions = [
            make_transaction(
                description="TESCO STORES",
                transaction_hash="hash_1",
            ),
            make_transaction(
                description="NETFLIX.COM",
                transaction_hash="hash_2",
            ),
            make_transaction(
                description="UNKNOWN",
                transaction_hash="hash_3",
            ),
        ]
        matched, unmatched = apply_rules(database, transactions)
        assert matched == 2
        assert unmatched == 1


class TestExtractPattern:
    def test_strips_direct_debit_prefix(self):
        pattern = _extract_pattern("DIRECT DEBIT PAYMENT TO BRITISH GAS, MANDATE NO 0001")
        assert pattern == "BRITISH GAS"

    def test_strips_trailing_comma_before_mandate(self):
        pattern = _extract_pattern(
            "DIRECT DEBIT PAYMENT TO PAYPAL PAYMENT REF 5Z722227M58B8, MANDATE NO 0006"
        )
        assert "," not in pattern

    def test_strips_card_payment_prefix(self):
        pattern = _extract_pattern("CARD PAYMENT TO TESCO STORES 2345")
        assert pattern == "TESCO STORES 2345"

    def test_strips_bill_payment_prefix_and_reference(self):
        pattern = _extract_pattern(
            "BILL PAYMENT VIA FASTER PAYMENT TO EE LIMITED REFERENCE 07700123456"
        )
        assert pattern == "EE LIMITED"

    def test_strips_transfer_prefix(self):
        pattern = _extract_pattern("TRANSFER FROM JAMIE LUKE MCMILLAN")
        assert pattern == "JAMIE LUKE MCMILLAN"

    def test_preserves_simple_description(self):
        pattern = _extract_pattern("GREGGS")
        assert pattern == "GREGGS"


class TestCreateRuleFromDescription:
    def test_creates_rule_with_extracted_pattern(self, database: DatabaseClient):
        rule = create_rule_from_description(
            database,
            "DIRECT DEBIT PAYMENT TO BRITISH GAS, MANDATE NO 0001",
            CategoryType.UTILITIES,
        )
        assert rule.pattern == "BRITISH GAS"
        assert rule.category == CategoryType.UTILITIES
        assert rule.source == "manual"

    def test_rule_persists_in_database(self, database: DatabaseClient):
        create_rule_from_description(
            database,
            "CARD PAYMENT TO TESCO STORES",
            CategoryType.GROCERIES,
        )
        rules = database.select_all(Rule)
        assert len(rules) == 1
        assert rules[0].pattern == "TESCO STORES"
