from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from finance_tracker.categories import SPENDING_BUCKETS, CategoryType, spending_categories
from finance_tracker.database import DatabaseClient
from finance_tracker.ingest import parse_santander_txt
from finance_tracker.models import Rule, Transaction
from finance_tracker.rules import (
    apply_rules,
    create_rule_from_description,
    extract_pattern,
    match_counts,
    reapply_rules,
)
from finance_tracker.visualise import (
    plot_budget_pie,
    plot_category_summary,
    plot_monthly_buckets,
    plot_monthly_trends,
    plot_weekly_breakdown,
)

app = typer.Typer(name="finance", help="Personal finance tracker")
console = Console()


@app.command(name="import")
def import_transactions(
    path: Path = typer.Argument(..., help="Path to Santander TXT file or directory of TXT files"),
    account: str = typer.Option(..., help="Account name (e.g. 'Everyday', 'Current')"),
) -> None:
    """Import transactions from a Santander TXT statement export."""
    if not path.exists():
        console.print(f"[red]Not found: {path}[/red]")
        raise typer.Exit(code=1)

    if path.is_dir():
        files = sorted(path.glob("*.txt"))
        if not files:
            console.print(f"[yellow]No .txt files found in {path}[/yellow]")
            raise typer.Exit()
    else:
        files = [path]

    transactions = []
    for file in files:
        parsed = parse_santander_txt(file, account)
        transactions.extend(parsed)
        console.print(f"  [dim]Parsed {len(parsed)} transactions from {file.name}[/dim]")

    if not transactions:
        console.print("[yellow]No transactions found.[/yellow]")
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
def categorise(
    auto_rules: bool = typer.Option(True, help="Default to yes when prompted to create rules"),
) -> None:
    """Interactively categorise uncategorised transactions."""
    with DatabaseClient.create() as database:
        uncategorised = database.select_where(
            Transaction, Transaction.category == CategoryType.UNCATEGORISED
        )

        if uncategorised:
            matched, _ = apply_rules(database, uncategorised)
            if matched:
                for matched_transaction in uncategorised:
                    if matched_transaction.category != CategoryType.UNCATEGORISED:
                        database.add(matched_transaction)
                console.print(f"[green]Auto-categorised {matched} transactions from rules[/green]")
                uncategorised = [
                    t for t in uncategorised if t.category == CategoryType.UNCATEGORISED
                ]

        if not uncategorised:
            console.print("[green]No uncategorised transactions.[/green]")
            return

        console.print(f"\n[bold]{len(uncategorised)} uncategorised transactions[/bold]\n")

        category_list = list(CategoryType)
        for transaction in uncategorised:
            if transaction.category != CategoryType.UNCATEGORISED:
                continue
            _display_transaction(transaction)
            _display_category_menu(category_list)

            choice = Prompt.ask(
                "Category number (or 's' to skip, 'x' to ignore, 'q' to quit)",
                default="s",
            )

            if choice.lower() == "q":
                break
            if choice.lower() == "s":
                continue
            if choice.lower() == "x":
                transaction.category = CategoryType.IGNORED
                database.add(transaction)
                console.print("  [dim]Ignored[/dim]\n")
                continue

            try:
                selected_category = category_list[int(choice) - 1]
            except ValueError, IndexError:
                console.print("[red]Invalid choice, skipping.[/red]")
                continue

            transaction.category = selected_category
            database.add(transaction)

            pattern = extract_pattern(transaction.description)
            console.print(f"  [dim]Rule: '{pattern}' → {selected_category.display_name}[/dim]")
            if Confirm.ask("Create this rule?", default=auto_rules):
                rule = create_rule_from_description(
                    database, transaction.description, selected_category
                )
                if rule is None:
                    console.print("  [dim]Rule already exists[/dim]")
                else:
                    remaining = [
                        t for t in uncategorised if t.category == CategoryType.UNCATEGORISED
                    ]
                    matched, _ = apply_rules(database, remaining)
                    for matched_transaction in remaining:
                        if matched_transaction.category != CategoryType.UNCATEGORISED:
                            database.add(matched_transaction)
                    if matched:
                        console.print(f"  [dim]Rule saved — auto-categorised {matched} more[/dim]")
                    else:
                        console.print("  [dim]Rule saved[/dim]")

            console.print()


rules_app = typer.Typer(help="Manage categorisation rules")
app.add_typer(rules_app, name="rules")


@rules_app.callback(invoke_without_command=True)
def rules_list(ctx: typer.Context) -> None:
    """List all categorisation rules with match counts."""
    if ctx.invoked_subcommand is not None:
        return

    with DatabaseClient.create() as database:
        all_rules = database.select_all(Rule)

        if not all_rules:
            console.print(
                "[yellow]No rules defined yet. Run 'finance categorise' to create some.[/yellow]"
            )
            raise typer.Exit()

        counts = match_counts(database)

        table = Table(title="Categorisation Rules")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Pattern", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Source", style="dim")
        table.add_column("Matches", justify="right")

        sorted_rules = sorted(all_rules, key=lambda r: counts.get(r.id, 0), reverse=True)
        for index, rule in enumerate(sorted_rules, 1):
            count = counts.get(rule.id, 0)
            count_display = f"[red]{count}[/red]" if count == 0 else str(count)
            table.add_row(
                str(index),
                rule.pattern,
                rule.category.display_name,
                rule.source,
                count_display,
            )

        console.print(table)

        zero_match = sum(1 for count in counts.values() if count == 0)
        if zero_match:
            console.print(
                f"\n[yellow]{zero_match} rules match no transactions. "
                f"Use 'finance rules delete' to clean up.[/yellow]"
            )


@rules_app.command()
def delete() -> None:
    """Interactively delete rules."""
    with DatabaseClient.create() as database:
        all_rules = database.select_all(Rule)

        if not all_rules:
            console.print("[yellow]No rules to delete.[/yellow]")
            raise typer.Exit()

        counts = match_counts(database)
        sorted_rules = sorted(all_rules, key=lambda r: counts.get(r.id, 0))

        for index, rule in enumerate(sorted_rules, 1):
            count = counts.get(rule.id, 0)
            count_style = "red" if count == 0 else "dim"
            console.print(
                f"  {index:3d}. {rule.pattern}  → {rule.category.display_name}  "
                f"[{count_style}]({count} matches)[/{count_style}]"
            )

        console.print()
        selection = Prompt.ask("Rule number(s) to delete (comma-separated, or 'q' to quit)")

        if selection.lower() == "q":
            return

        try:
            indices = [int(s.strip()) for s in selection.split(",")]
        except ValueError:
            console.print("[red]Invalid input.[/red]")
            return

        to_delete = []
        for index in indices:
            if 1 <= index <= len(sorted_rules):
                to_delete.append(sorted_rules[index - 1])
            else:
                console.print(f"[red]Invalid rule number: {index}[/red]")
                return

        console.print()
        for rule in to_delete:
            console.print(f"  [red]- {rule.pattern} → {rule.category.display_name}[/red]")

        if not Confirm.ask(f"\nDelete {len(to_delete)} rule(s)?", default=False):
            return

        for rule in to_delete:
            database.delete(rule)
        console.print(f"[green]Deleted {len(to_delete)} rule(s).[/green]")


@rules_app.command()
def edit() -> None:
    """Interactively edit a rule's pattern or category."""
    with DatabaseClient.create() as database:
        all_rules = database.select_all(Rule)

        if not all_rules:
            console.print("[yellow]No rules to edit.[/yellow]")
            raise typer.Exit()

        counts = match_counts(database)
        sorted_rules = sorted(all_rules, key=lambda r: (r.category.display_name, r.pattern))

        for index, rule in enumerate(sorted_rules, 1):
            count = counts.get(rule.id, 0)
            console.print(
                f"  {index:3d}. {rule.pattern}  → {rule.category.display_name}  "
                f"[dim]({count} matches)[/dim]"
            )

        console.print()
        selection = Prompt.ask("Rule number to edit (or 'q' to quit)")

        if selection.lower() == "q":
            return

        try:
            index = int(selection)
        except ValueError:
            console.print("[red]Invalid input.[/red]")
            return

        if not 1 <= index <= len(sorted_rules):
            console.print("[red]Invalid rule number.[/red]")
            return

        rule = sorted_rules[index - 1]
        console.print(f"\n  Pattern:  [cyan]{rule.pattern}[/cyan]")
        console.print(f"  Category: [green]{rule.category.display_name}[/green]\n")

        new_pattern = Prompt.ask("New pattern", default=rule.pattern)

        category_list = list(CategoryType)
        _display_category_menu(category_list)
        current_index = category_list.index(rule.category) + 1
        category_choice = Prompt.ask("New category number", default=str(current_index))

        try:
            new_category = category_list[int(category_choice) - 1]
        except ValueError, IndexError:
            console.print("[red]Invalid category.[/red]")
            return

        if new_pattern == rule.pattern and new_category == rule.category:
            console.print("[dim]No changes.[/dim]")
            return

        rule.pattern = new_pattern
        rule.category = new_category
        database.add(rule)

        new_counts = match_counts(database)
        new_count = new_counts.get(rule.id, 0)
        console.print(
            f"[green]Updated: '{rule.pattern}' → {rule.category.display_name} "
            f"({new_count} matches)[/green]"
        )


@rules_app.command()
def apply() -> None:
    """Re-apply all rules to transactions."""
    with DatabaseClient.create() as database:
        applied, conflicts = reapply_rules(database)

        if applied:
            console.print(f"[green]Categorised {len(applied)} uncategorised transactions:[/green]")
            for transaction in applied:
                _display_transaction(transaction)
                console.print(f"    → [green]{transaction.category.display_name}[/green]")
        else:
            console.print("[dim]No uncategorised transactions matched any rules.[/dim]")

        if conflicts:
            console.print(
                f"\n[yellow]{len(conflicts)} already-categorised transactions "
                f"would change:[/yellow]"
            )
            for transaction, suggested in conflicts:
                _display_transaction(transaction)
                console.print(
                    f"    [dim]current:[/dim] {transaction.category.display_name}"
                    f"  [dim]→ rule suggests:[/dim] [yellow]{suggested.display_name}[/yellow]"
                )


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
            if transaction.category.bucket not in SPENDING_BUCKETS:
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
def trends(
    category: str = typer.Option(None, help="Filter to a specific category (e.g. 'GROCERIES')"),
    save: str = typer.Option(None, help="Save chart to file instead of displaying"),
) -> None:
    """Show monthly spending trend lines."""
    with DatabaseClient.create() as database:
        transactions = database.select_all(Transaction)

        if not transactions:
            console.print("[yellow]No transactions imported yet.[/yellow]")
            raise typer.Exit()

        category_filter = None
        if category:
            try:
                category_filter = CategoryType[category.upper()]
            except KeyError:
                console.print(f"[red]Unknown category: {category}[/red]")
                raise typer.Exit(code=1) from None

        plot_monthly_trends(transactions, category=category_filter, save_path=save)


@app.command()
def plot(
    chart: str = typer.Argument(..., help="Chart type: categories, budget, buckets, weekly"),
    weeks: int = typer.Option(12, help="Number of weeks for weekly chart"),
    save: str = typer.Option(None, help="Save chart to file instead of displaying"),
) -> None:
    """Generate spending visualisations."""
    with DatabaseClient.create() as database:
        transactions = database.select_all(Transaction)

        if not transactions:
            console.print("[yellow]No transactions imported yet.[/yellow]")
            raise typer.Exit()

        chart_functions = {
            "categories": lambda: plot_category_summary(transactions, save_path=save),
            "budget": lambda: plot_budget_pie(transactions, save_path=save),
            "buckets": lambda: plot_monthly_buckets(transactions, save_path=save),
            "weekly": lambda: plot_weekly_breakdown(
                transactions, last_n_weeks=weeks, save_path=save
            ),
        }

        if chart not in chart_functions:
            console.print(
                f"[red]Unknown chart type: {chart}[/red]\nAvailable: {', '.join(chart_functions)}"
            )
            raise typer.Exit(code=1)

        chart_functions[chart]()


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
        if category in spending:
            console.print(f"    {index:2d}. {category.display_name}")
        else:
            console.print(f"    [dim]{index:2d}. {category.display_name}[/dim]")
    console.print()
