from finance_tracker.categories import CategoryType
from finance_tracker.database import DatabaseClient
from finance_tracker.models import Rule
from finance_tracker.seeds import SEED_RULES, build_seed_rules


class TestBuildSeedRules:
    def test_returns_rule_for_each_seed_entry(self):
        rules = build_seed_rules()
        assert len(rules) == len(SEED_RULES)

    def test_all_rules_have_seed_source(self):
        rules = build_seed_rules()
        assert all(rule.source == "seed" for rule in rules)

    def test_all_patterns_are_non_empty(self):
        rules = build_seed_rules()
        assert all(rule.pattern for rule in rules)

    def test_all_categories_are_valid(self):
        rules = build_seed_rules()
        assert all(isinstance(rule.category, CategoryType) for rule in rules)

    def test_no_duplicate_patterns(self):
        patterns = [pattern for pattern, _ in SEED_RULES]
        assert len(patterns) == len(set(patterns))


class TestSeedOnDatabaseCreation:
    def test_new_database_has_seed_rules(self, tmp_path):
        db_path = tmp_path / "test.db"
        with DatabaseClient.create(db_path=db_path) as database:
            rules = database.select_all(Rule)
            assert len(rules) == len(SEED_RULES)
            seed_sources = [rule for rule in rules if rule.source == "seed"]
            assert len(seed_sources) == len(SEED_RULES)

    def test_existing_database_does_not_reseed(self, tmp_path):
        db_path = tmp_path / "test.db"
        with DatabaseClient.create(db_path=db_path) as database:
            first_count = len(database.select_all(Rule))

        with DatabaseClient.create(db_path=db_path) as database:
            second_count = len(database.select_all(Rule))

        assert first_count == second_count

    def test_seed_rules_do_not_conflict_with_manual_rules(self, tmp_path):
        db_path = tmp_path / "test.db"
        with DatabaseClient.create(db_path=db_path) as database:
            manual_rule = Rule(
                pattern="MY LOCAL SHOP", category=CategoryType.GROCERIES, source="manual"
            )
            database.add(manual_rule)
            total_rules = len(database.select_all(Rule))
            assert total_rules == len(SEED_RULES) + 1

    def test_null_database_has_no_seed_rules(self):
        with DatabaseClient.create_null() as database:
            rules = database.select_all(Rule)
            assert len(rules) == 0
