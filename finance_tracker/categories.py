from enum import Enum


class Bucket(Enum):
    NEED = "need"
    WANT = "want"
    SAVINGS = "savings"
    EXCLUDED = "excluded"


class CategoryType(Enum):
    GROCERIES = ("Groceries", Bucket.NEED)
    HOUSING = ("Housing", Bucket.NEED)
    UTILITIES = ("Utilities", Bucket.NEED)
    TRANSPORT = ("Transport", Bucket.NEED)
    INSURANCE = ("Insurance", Bucket.NEED)
    PHONE_INTERNET = ("Phone & Internet", Bucket.NEED)
    HEALTHCARE = ("Healthcare", Bucket.NEED)
    CHILDCARE_EDUCATION = ("Childcare & Education", Bucket.NEED)
    EATING_OUT = ("Eating Out", Bucket.WANT)
    ENTERTAINMENT = ("Entertainment", Bucket.WANT)
    SHOPPING = ("Shopping", Bucket.WANT)
    SUBSCRIPTIONS = ("Subscriptions", Bucket.WANT)
    HOLIDAYS_TRAVEL = ("Holidays & Travel", Bucket.WANT)
    GIFTS_CHARITY = ("Gifts & Charity", Bucket.WANT)
    PETS = ("Pets", Bucket.WANT)
    PERSONAL_BUSINESS = ("Personal Business", Bucket.NEED)
    SAVINGS_INVESTMENTS = ("Savings & Investments", Bucket.SAVINGS)
    DEBT_REPAYMENT = ("Debt Repayment", Bucket.SAVINGS)
    INCOME = ("Income", Bucket.EXCLUDED)
    TRANSFER = ("Transfer", Bucket.EXCLUDED)
    UNCATEGORISED = ("Uncategorised", Bucket.EXCLUDED)

    def __init__(self, display_name: str, bucket: Bucket) -> None:
        self.display_name = display_name
        self.bucket = bucket


SPENDING_BUCKETS = {Bucket.NEED, Bucket.WANT, Bucket.SAVINGS}


def spending_categories() -> list[CategoryType]:
    return [c for c in CategoryType if c.bucket in SPENDING_BUCKETS]
