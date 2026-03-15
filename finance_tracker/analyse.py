from collections import defaultdict
from collections.abc import Sequence
from datetime import date

from finance_tracker.categories import SPENDING_BUCKETS, Bucket, CategoryType
from finance_tracker.models import Transaction


def spending_by_category(
    transactions: Sequence[Transaction],
) -> dict[CategoryType, float]:
    totals: dict[CategoryType, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        totals[transaction.category] += abs(transaction.amount)
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def spending_by_bucket(
    transactions: Sequence[Transaction],
) -> dict[Bucket, float]:
    totals: dict[Bucket, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        bucket = transaction.category.bucket
        if bucket in SPENDING_BUCKETS:
            totals[bucket] += abs(transaction.amount)
    return dict(totals)


def monthly_spending(
    transactions: Sequence[Transaction],
) -> dict[str, dict[CategoryType, float]]:
    """Group spending by month (YYYY-MM) and category."""
    monthly: dict[str, dict[CategoryType, float]] = defaultdict(lambda: defaultdict(float))
    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        month_key = transaction.transaction_date.strftime("%Y-%m")
        monthly[month_key][transaction.category] += abs(transaction.amount)
    return dict(sorted(monthly.items()))


def monthly_bucket_spending(
    transactions: Sequence[Transaction],
) -> dict[str, dict[Bucket, float]]:
    """Group spending by month and bucket (need/want/savings)."""
    monthly: dict[str, dict[Bucket, float]] = defaultdict(lambda: defaultdict(float))
    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        bucket = transaction.category.bucket
        if bucket in SPENDING_BUCKETS:
            month_key = transaction.transaction_date.strftime("%Y-%m")
            monthly[month_key][bucket] += abs(transaction.amount)
    return dict(sorted(monthly.items()))


def weekly_spending(
    transactions: Sequence[Transaction],
    last_n_weeks: int | None = None,
) -> dict[str, dict[CategoryType, float]]:
    """Group spending by ISO week (YYYY-Wnn) and category."""
    weekly: dict[str, dict[CategoryType, float]] = defaultdict(lambda: defaultdict(float))
    for transaction in transactions:
        if transaction.amount >= 0:
            continue
        week_key = transaction.transaction_date.strftime("%G-W%V")
        weekly[week_key][transaction.category] += abs(transaction.amount)

    sorted_weeks = dict(sorted(weekly.items()))
    if last_n_weeks:
        keys = list(sorted_weeks.keys())[-last_n_weeks:]
        sorted_weeks = {k: sorted_weeks[k] for k in keys}
    return sorted_weeks


def total_income(transactions: Sequence[Transaction]) -> float:
    return sum(t.amount for t in transactions if t.amount > 0)


def total_spending(transactions: Sequence[Transaction]) -> float:
    return sum(abs(t.amount) for t in transactions if t.amount < 0)


def date_range(transactions: Sequence[Transaction]) -> tuple[date, date] | None:
    dates = [t.transaction_date for t in transactions]
    if not dates:
        return None
    return min(dates), max(dates)
