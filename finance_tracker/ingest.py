import hashlib
import re
from datetime import date
from pathlib import Path

from finance_tracker.models import Transaction


def parse_santander_txt(file_path: Path, account: str) -> list[Transaction]:
    """Parse a Santander TXT statement export into Transaction model instances."""
    content = file_path.read_text(encoding="iso-8859-1")
    lines = content.splitlines()

    transactions: list[Transaction] = []
    current_block: dict[str, str] = {}

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(("From:", "Account:", "Arranged overdraft")):
            continue

        field_match = re.match(r"^(Date|Description|Amount|Balance):\s*(.+)", stripped)
        if field_match:
            field_name = field_match.group(1)
            field_value = field_match.group(2).strip()
            current_block[field_name] = field_value
            continue

        if not stripped and current_block:
            transaction = _build_transaction(current_block, account)
            if transaction:
                transactions.append(transaction)
            current_block = {}

    if current_block:
        transaction = _build_transaction(current_block, account)
        if transaction:
            transactions.append(transaction)

    return transactions


def _build_transaction(block: dict[str, str], account: str) -> Transaction | None:
    required_fields = {"Date", "Description", "Amount", "Balance"}
    if not required_fields.issubset(block.keys()):
        return None

    transaction_date = _parse_date(block["Date"])
    description = block["Description"]
    amount = _parse_amount(block["Amount"])
    balance = _parse_amount(block["Balance"])
    transaction_hash = _compute_hash(transaction_date, description, amount, balance)

    return Transaction(
        transaction_date=transaction_date,
        description=description,
        amount=amount,
        balance=balance,
        account=account,
        transaction_hash=transaction_hash,
    )


def _parse_date(raw: str) -> date:
    cleaned = re.sub(r"[^\d/]", "", raw)
    day, month, year = cleaned.split("/")
    return date(int(year), int(month), int(day))


def _parse_amount(raw: str) -> float:
    cleaned = re.sub(r"[^\d.\-+]", "", raw)
    return float(cleaned)


def _compute_hash(transaction_date: date, description: str, amount: float, balance: float) -> str:
    raw = f"{transaction_date.isoformat()}|{description}|{amount:.2f}|{balance:.2f}"
    return hashlib.sha256(raw.encode()).hexdigest()
