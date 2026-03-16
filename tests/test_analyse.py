from finance_tracker.analyse import (
    date_range,
    monthly_spending,
    spending_by_bucket,
    spending_by_category,
    total_income,
    total_spending,
    weekly_spending,
)
from finance_tracker.categories import Bucket, CategoryType
from finance_tracker.models import Transaction


class TestSpendingByCategory:
    def test_groups_outgoings_by_category(self, sample_transactions: list[Transaction]):
        result = spending_by_category(sample_transactions)
        assert result[CategoryType.GROCERIES] == 67.43 + 92.17

    def test_excludes_income(self, sample_transactions: list[Transaction]):
        result = spending_by_category(sample_transactions)
        assert CategoryType.INCOME not in result

    def test_sorted_by_amount_descending(self, sample_transactions: list[Transaction]):
        result = spending_by_category(sample_transactions)
        amounts = list(result.values())
        assert amounts == sorted(amounts, reverse=True)


class TestSpendingByBucket:
    def test_sums_needs(self, sample_transactions: list[Transaction]):
        result = spending_by_bucket(sample_transactions)
        needs = 85.00 + 67.43 + 55.00 + 92.17 + 45.50
        assert abs(result[Bucket.NEED] - needs) < 0.01

    def test_sums_wants(self, sample_transactions: list[Transaction]):
        result = spending_by_bucket(sample_transactions)
        wants = 18.99 + 15.99 + 29.99 + 350.00
        assert abs(result[Bucket.WANT] - wants) < 0.01

    def test_sums_savings(self, sample_transactions: list[Transaction]):
        result = spending_by_bucket(sample_transactions)
        assert result[Bucket.SAVINGS] == 200.00

    def test_excludes_excluded_bucket(self, sample_transactions: list[Transaction]):
        result = spending_by_bucket(sample_transactions)
        assert Bucket.EXCLUDED not in result


class TestMonthlySpending:
    def test_groups_by_month(self, sample_transactions: list[Transaction]):
        result = monthly_spending(sample_transactions)
        assert "2026-01" in result
        assert "2026-02" in result

    def test_months_sorted_chronologically(self, sample_transactions: list[Transaction]):
        result = monthly_spending(sample_transactions)
        months = list(result.keys())
        assert months == sorted(months)


class TestWeeklySpending:
    def test_limits_to_last_n_weeks(self, sample_transactions: list[Transaction]):
        result = weekly_spending(sample_transactions, last_n_weeks=1)
        assert len(result) == 1


class TestTotals:
    def test_total_income(self, sample_transactions: list[Transaction]):
        result = total_income(sample_transactions)
        assert result == 2500.00

    def test_total_spending(self, sample_transactions: list[Transaction]):
        result = total_spending(sample_transactions)
        expected = 85.00 + 67.43 + 18.99 + 15.99 + 55.00 + 92.17 + 45.50 + 29.99 + 200.00 + 350.00
        assert abs(result - expected) < 0.01


class TestTransferExclusion:
    def test_transfers_excluded_from_spending_by_category(self, sample_transactions):
        result = spending_by_category(sample_transactions)
        assert CategoryType.TRANSFER not in result

    def test_transfers_excluded_from_total_spending(self, sample_transactions):
        result = total_spending(sample_transactions)
        expected_without_transfer = (
            85.00 + 67.43 + 18.99 + 15.99 + 55.00 + 92.17 + 45.50 + 29.99 + 200.00 + 350.00
        )
        assert abs(result - expected_without_transfer) < 0.01

    def test_transfers_excluded_from_total_income(self, sample_transactions):
        result = total_income(sample_transactions)
        assert result == 2500.00

    def test_transfers_excluded_from_monthly_spending(self, sample_transactions):
        result = monthly_spending(sample_transactions)
        for month_data in result.values():
            assert CategoryType.TRANSFER not in month_data

    def test_transfers_excluded_from_weekly_spending(self, sample_transactions):
        result = weekly_spending(sample_transactions)
        for week_data in result.values():
            assert CategoryType.TRANSFER not in week_data

    def test_transfers_excluded_from_spending_by_bucket(self, sample_transactions):
        result = spending_by_bucket(sample_transactions)
        assert Bucket.EXCLUDED not in result


class TestDateRange:
    def test_returns_min_and_max(self, sample_transactions: list[Transaction]):
        result = date_range(sample_transactions)
        assert result is not None
        start, end = result
        assert start.month == 1
        assert end.month == 2

    def test_returns_none_for_empty(self):
        assert date_range([]) is None
