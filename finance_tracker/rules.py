import re
from collections.abc import Sequence

from finance_tracker.categories import CategoryType
from finance_tracker.database import DatabaseClient
from finance_tracker.models import Rule, Transaction


def apply_rules(database: DatabaseClient, transactions: Sequence[Transaction]) -> tuple[int, int]:
    """Apply all stored rules to uncategorised transactions. Returns (matched, unmatched)."""
    rules = database.select_all(Rule)
    matched = 0
    unmatched = 0

    for transaction in transactions:
        if transaction.category != CategoryType.UNCATEGORISED:
            matched += 1
            continue

        category = _match_rules(transaction.description, rules)
        if category:
            transaction.category = category
            matched += 1
        else:
            unmatched += 1

    return matched, unmatched


def _match_rules(description: str, rules: Sequence[Rule]) -> CategoryType | None:
    upper_description = description.upper()
    for rule in rules:
        if re.search(rule.pattern, upper_description, re.IGNORECASE):
            return rule.category
    return None


def create_rule_from_description(
    database: DatabaseClient,
    description: str,
    category: CategoryType,
) -> Rule | None:
    """Extract a keyword pattern from a description and save as a rule.

    Returns None if a rule with the same pattern already exists.
    """
    pattern = extract_pattern(description)
    rule = Rule(pattern=pattern, category=category, source="manual")
    inserted = database.add_if_new(rule)
    return rule if inserted else None


def extract_pattern(description: str) -> str:
    """Extract the most meaningful part of a transaction description for reuse as a rule.

    Strips common prefixes like DIRECT DEBIT PAYMENT TO, BILL PAYMENT VIA FASTER PAYMENT TO,
    TRANSFER FROM, etc. to get the merchant/payee name.
    """
    prefixes_to_strip = [
        r"DIRECT DEBIT PAYMENT TO\s+",
        r"BILL PAYMENT VIA FASTER PAYMENT TO\s+",
        r"CARD PAYMENT TO\s+",
        r"TRANSFER FROM\s+",
        r"TRANSFER TO\s+",
        r"STANDING ORDER TO\s+",
        r"SQ\s*\*\s*",
        r"SUMUP\s*\*\s*",
        r"SP\s+\*\s*",
        r"SP\s+",
    ]
    cleaned = description.strip()
    for prefix in prefixes_to_strip:
        cleaned = re.sub(f"^{prefix}", "", cleaned, flags=re.IGNORECASE)

    suffixes_to_strip = [
        r"[,\s]+(REFERENCE|REF|MANDATE NO)\s+.*$",
        r"[,\s]+[\d.]+\s*GBP,\s*RATE\s+[\d./]+GBP\s+ON\s+[\d-]+$",
        r"\s*\(VIA\s+\w+\s+PAY\).*$",
        r"\s+ON\s+\d{2}-\d{2}-\d{4}$",
    ]
    for suffix in suffixes_to_strip:
        cleaned = re.sub(suffix, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip().rstrip(",")
