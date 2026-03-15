from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from finance_tracker.categories import CategoryType, spending_categories
from finance_tracker.database import DatabaseClient
from finance_tracker.ingest import parse_santander_txt
from finance_tracker.models import Rule, Transaction
from finance_tracker.rules import apply_rules, create_rule_from_description

app = typer.Typer(name="finance", help="Personal finance tracker")
console = Console()


@app.command(name="import")
def import_transactions(
    file_path: Path = typer.Argument(..., help="Path to Santander TXT statement file"),
    account: str = typer.Option(..., help="Account name (e.g. 'Everyday', 'Current')"),
) -> None:
    """Import transactions from a Santander TXT statement export."""
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(code=1)

    transactions = parse_santander_txt(file_path, account)
    if not transactions:
        console.print("[yellow]No transactions found in file.[/yellow]")
        raise typer.Exit()

    with DatabaseClient.create() as database:
        matched, unmatched = apply_rules(database, transactions)

        inserted = 0
        skipped = 0
        for transaction in transactions:
            transaction_result = database.add_if_new(transaction)
            if transaction_result:
                inserted += 1
            else:
                skipped += 1

        console.print(
            f"[green]Imported {inserted} transactions ({skipped} duplicates skipped)[/green]"
        )
        console.print(f"  Categorised: {matched} | Needs review: {unmatched}")


@app.command()
def categorise() -> None:
    """Interactively categorise uncategorised transactions."""
    with DatabaseClient.create() as database:
        uncategorised = database.select_where(
            Transaction, Transaction.category == CategoryType.UNCATEGORISED
        )

        if not uncategorised:
            console.print("[green]No uncategorised transactions.[/green]")
            raise typer.Exit()

        console.print(f"\n[bold]{len(uncategorised)} uncategorised transactions[/bold]\n")

        category_list = list(CategoryType)
        for transaction in uncategorised:
            _display_transaction(transaction)
            _display_category_menu(category_list)

            choice = Prompt.ask(
                "Category number (or 's' to skip, 'q' to quit)",
                default="s",
            )

            if choice.lower() == "q":
                break
            if choice.lower() == "s":
                continue

            try:
                selected_category = category_list[int(choice) - 1]
            except ValueError, IndexError:
                console.print("[red]Invalid choice, skipping.[/red]")
                continue

            transaction.category = selected_category
            database.add(transaction)

            if Confirm.ask("Create rule for similar transactions?", default=True):
                rule = create_rule_from_description(
                    database, transaction.description, selected_category
                )
                console.print(
                    f"  [dim]Rule saved: '{rule.pattern}' → {selected_category.display_name}[/dim]"
                )

            console.print()


@app.command()
def rules() -> None:
    """List all categorisation rules."""
    with DatabaseClient.create() as database:
        all_rules = database.select_all(Rule)

        if not all_rules:
            console.print(
                "[yellow]No rules defined yet. Run 'finance categorise' to create some.[/yellow]"
            )
            raise typer.Exit()

        table = Table(title="Categorisation Rules")
        table.add_column("Pattern", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Source", style="dim")

        for rule in all_rules:
            table.add_row(rule.pattern, rule.category.display_name, rule.source)

        console.print(table)


@app.command()
def summary() -> None:
    """Show spending summary by category."""
    with DatabaseClient.create() as database:
        transactions = database.select_all(Transaction)

        if not transactions:
            console.print("[yellow]No transactions imported yet.[/yellow]")
            raise typer.Exit()

        spending = {}
        for transaction in transactions:
            if transaction.amount >= 0:
                continue
            category = transaction.category
            spending[category] = spending.get(category, 0.0) + abs(transaction.amount)

        table = Table(title="Spending Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Bucket", style="dim")
        table.add_column("Total", justify="right", style="red")

        sorted_spending = sorted(spending.items(), key=lambda item: item[1], reverse=True)
        total = 0.0
        for category, amount in sorted_spending:
            table.add_row(category.display_name, category.bucket.value, f"£{amount:.2f}")
            total += amount

        table.add_section()
        table.add_row("[bold]Total[/bold]", "", f"[bold]£{total:.2f}[/bold]")
        console.print(table)


@app.command()
def budget() -> None:
    """Show 50/30/20 budget breakdown."""
    with DatabaseClient.create() as database:
        transactions = database.select_all(Transaction)

        if not transactions:
            console.print("[yellow]No transactions imported yet.[/yellow]")
            raise typer.Exit()

        bucket_totals = {"need": 0.0, "want": 0.0, "savings": 0.0}
        for transaction in transactions:
            if transaction.amount >= 0:
                continue
            bucket = transaction.category.bucket.value
            if bucket in bucket_totals:
                bucket_totals[bucket] += abs(transaction.amount)

        total_spending = sum(bucket_totals.values())
        if total_spending == 0:
            console.print("[yellow]No categorised spending found.[/yellow]")
            raise typer.Exit()

        table = Table(title="50/30/20 Budget Analysis")
        table.add_column("Bucket", style="cyan")
        table.add_column("Spent", justify="right")
        table.add_column("Actual %", justify="right")
        table.add_column("Target %", justify="right", style="dim")

        targets = {"need": 50, "want": 30, "savings": 20}
        for bucket_name, amount in bucket_totals.items():
            percentage = (amount / total_spending) * 100
            target = targets[bucket_name]
            colour = "green" if percentage <= target else "red"
            table.add_row(
                bucket_name.title(),
                f"£{amount:.2f}",
                f"[{colour}]{percentage:.1f}%[/{colour}]",
                f"{target}%",
            )

        table.add_section()
        table.add_row("[bold]Total[/bold]", f"[bold]£{total_spending:.2f}[/bold]", "", "")
        console.print(table)


@app.command()
def clear_data() -> None:
    """Drop all transactions but keep categorisation rules."""
    if not Confirm.ask(
        "[red]Delete all transactions?[/red] Rules will be preserved.", default=False
    ):
        raise typer.Exit()

    with DatabaseClient.create() as database:
        count = database.clear_table(Transaction)
        console.print(f"[green]Deleted {count} transactions. Rules preserved.[/green]")


@app.command()
def purge() -> None:
    """Remove all finance tracker data (~/.finance-tracker/)."""
    if not Confirm.ask(
        "[red]Delete ALL data including rules?[/red] This cannot be undone.", default=False
    ):
        raise typer.Exit()

    DatabaseClient.purge()
    console.print("[green]All data removed.[/green]")


def _display_transaction(transaction: Transaction) -> None:
    colour = "red" if transaction.amount < 0 else "green"
    console.print(
        f"  [dim]{transaction.transaction_date}[/dim]  "
        f"[{colour}]£{abs(transaction.amount):.2f}[/{colour}]  "
        f"{transaction.description}  "
        f"[dim]({transaction.account})[/dim]"
    )


def _display_category_menu(categories: list[CategoryType]) -> None:
    spending = spending_categories()
    console.print()
    for index, category in enumerate(categories, 1):
        marker = "  " if category in spending else "[dim]"
        suffix = "[/dim]" if category not in spending else ""
        console.print(f"  {marker}{index:2d}. {category.display_name}{suffix}")
    console.print()
