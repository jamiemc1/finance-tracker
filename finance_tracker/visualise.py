from collections.abc import Sequence

import matplotlib.pyplot as plt

from finance_tracker.analyse import (
    monthly_bucket_spending,
    monthly_spending,
    spending_by_bucket,
    spending_by_category,
    weekly_spending,
)
from finance_tracker.categories import SPENDING_BUCKETS, Bucket, CategoryType
from finance_tracker.models import Transaction

BUCKET_COLOURS = {
    Bucket.NEED: "#e74c3c",
    Bucket.WANT: "#f39c12",
    Bucket.SAVINGS: "#2ecc71",
}


def plot_category_summary(
    transactions: Sequence[Transaction],
    save_path: str | None = None,
) -> None:
    """Horizontal bar chart of spending by category."""
    totals = spending_by_category(transactions)
    spending_totals = {k: v for k, v in totals.items() if k.bucket in SPENDING_BUCKETS}

    if not spending_totals:
        return

    categories = list(spending_totals.keys())
    amounts = list(spending_totals.values())
    colours = [BUCKET_COLOURS[c.bucket] for c in categories]
    labels = [c.display_name for c in categories]

    fig, axis = plt.subplots(figsize=(10, max(4, len(categories) * 0.4)))
    axis.barh(labels, amounts, color=colours)
    axis.set_xlabel("Spend (£)")
    axis.set_title("Spending by Category")
    axis.invert_yaxis()

    for index, amount in enumerate(amounts):
        axis.text(amount + 1, index, f"£{amount:.0f}", va="center", fontsize=8)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    plt.close(fig)


def plot_budget_pie(
    transactions: Sequence[Transaction],
    save_path: str | None = None,
) -> None:
    """Pie chart of need/want/savings split."""
    totals = spending_by_bucket(transactions)
    if not totals:
        return

    labels = [b.value.title() for b in totals]
    amounts = list(totals.values())
    colours = [BUCKET_COLOURS[b] for b in totals]

    fig, axis = plt.subplots(figsize=(8, 6))
    axis.pie(
        amounts,
        labels=labels,
        colors=colours,
        autopct="%1.1f%%",
        startangle=90,
    )
    axis.set_title("50/30/20 Budget Split")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    plt.close(fig)


def plot_monthly_trends(
    transactions: Sequence[Transaction],
    category: CategoryType | None = None,
    save_path: str | None = None,
) -> None:
    """Line chart of monthly spending trends."""
    monthly = monthly_spending(transactions)
    if not monthly:
        return

    months = list(monthly.keys())

    if category:
        amounts = [monthly[m].get(category, 0.0) for m in months]
        fig, axis = plt.subplots(figsize=(12, 5))
        axis.plot(months, amounts, marker="o", linewidth=2, label=category.display_name)
        axis.set_title(f"Monthly Spending: {category.display_name}")
    else:
        all_categories = set()
        for month_data in monthly.values():
            all_categories.update(c for c in month_data if c.bucket in SPENDING_BUCKETS)

        top_categories = sorted(
            all_categories,
            key=lambda c: sum(monthly[m].get(c, 0.0) for m in months),
            reverse=True,
        )[:8]

        fig, axis = plt.subplots(figsize=(12, 6))
        for cat in top_categories:
            amounts = [monthly[m].get(cat, 0.0) for m in months]
            axis.plot(months, amounts, marker="o", linewidth=1.5, label=cat.display_name)
        axis.set_title("Monthly Spending by Category (Top 8)")
        axis.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)

    axis.set_xlabel("Month")
    axis.set_ylabel("Spend (£)")
    axis.tick_params(axis="x", rotation=45)
    axis.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    plt.close(fig)


def plot_monthly_buckets(
    transactions: Sequence[Transaction],
    save_path: str | None = None,
) -> None:
    """Stacked bar chart of need/want/savings per month."""
    monthly = monthly_bucket_spending(transactions)
    if not monthly:
        return

    months = list(monthly.keys())
    buckets = [Bucket.NEED, Bucket.WANT, Bucket.SAVINGS]

    fig, axis = plt.subplots(figsize=(12, 6))
    bottom = [0.0] * len(months)

    for bucket in buckets:
        amounts = [monthly[m].get(bucket, 0.0) for m in months]
        axis.bar(
            months,
            amounts,
            bottom=bottom,
            label=bucket.value.title(),
            color=BUCKET_COLOURS[bucket],
        )
        bottom = [b + a for b, a in zip(bottom, amounts, strict=True)]

    axis.set_xlabel("Month")
    axis.set_ylabel("Spend (£)")
    axis.set_title("Monthly Spending: Needs vs Wants vs Savings")
    axis.legend()
    axis.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    plt.close(fig)


def plot_weekly_breakdown(
    transactions: Sequence[Transaction],
    last_n_weeks: int = 12,
    save_path: str | None = None,
) -> None:
    """Stacked bar chart of weekly spending by category."""
    weekly = weekly_spending(transactions, last_n_weeks=last_n_weeks)
    if not weekly:
        return

    weeks = list(weekly.keys())

    all_categories = set()
    for week_data in weekly.values():
        all_categories.update(c for c in week_data if c.bucket in SPENDING_BUCKETS)

    top_categories = sorted(
        all_categories,
        key=lambda c: sum(weekly[w].get(c, 0.0) for w in weeks),
        reverse=True,
    )[:8]

    fig, axis = plt.subplots(figsize=(14, 6))
    bottom = [0.0] * len(weeks)

    for cat in top_categories:
        amounts = [weekly[w].get(cat, 0.0) for w in weeks]
        axis.bar(weeks, amounts, bottom=bottom, label=cat.display_name)
        bottom = [b + a for b, a in zip(bottom, amounts, strict=True)]

    axis.set_xlabel("Week")
    axis.set_ylabel("Spend (£)")
    axis.set_title(f"Weekly Spending Breakdown (Last {last_n_weeks} Weeks)")
    axis.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    axis.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    plt.close(fig)
