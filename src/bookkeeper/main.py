#!/usr/bin/env python

# TODO: eventually this system should allow inserting these records to a
# web-backend.
import click
import os.path
import pathlib
import os
import re
from bookkeeper import txparser
from bookkeeper import defparser
from bookkeeper import ledger


def output_general_ledger(ledger, output):
    for account in sorted(ledger.accounts.values(),
                          key=lambda acc: acc.number):
        if not account.entries:
            continue

        print(f"{account.number:4} {account.name}", file=output)
        cumulative = 0
        for entry in account.entries:
            cumulative += entry.change

            description = entry.description or entry.transaction.description
            if len(description) > 39:
                description = description[:36] + "..."

            print(f"{entry.transaction.id:>6}"
                  f" {description:39}"
                  f" {entry.transaction.date}"
                  f" {entry.change:>10,}"
                  f" {cumulative:>10,}",
                  file=output)
        sep = "========="
        print(f"{sep:>79}", file=output)
        print(f"{account.balance:>79,}", file=output)


def output_statement(entity, output):
    def print_block(block, out, indent=0, width=68, change_sign=False):
        if block.sum() == 0:
            return

        given_indent = indent
        indent = given_indent if given_indent > 0 else 0
        ind = " " * 2 * indent

        print(f"{ind}{block.title}", file=out)

        name_width = width - 2 * indent - 1 - 10 - 12
        summary_width = width - 2 * indent - 1 - 10

        multiplier = -1 if change_sign else 1

        acc = 0
        for member in block.members:
            acc += member.sum()
            if isinstance(member, ledger.Block):
                print_block(member, out, indent=given_indent + 1,
                            change_sign=change_sign)
            elif isinstance(member, ledger.SummaryLine):
                print(
                    f"{ind}{member.summary:{summary_width}} "
                    f"{multiplier * acc:>10,}",
                    file=out)
            else:
                assert (isinstance(member, ledger.Account) or
                        isinstance(member, ledger.Profit)), \
                    f"Unexcepted type, got {type(member)}"
                if member.sum() != 0:
                    print(
                        f"{ind}  {member.description():{name_width}} "
                        f"{multiplier * member.sum():>10,}",
                        file=out)
        print(
            f"{ind}{block.summary:{summary_width}} "
            f"{multiplier * block.sum():>10,}",
            file=out)

    print(f"{entity.name}   {entity.fiscal_year_start} - "
          f"{entity.fiscal_year_end}\n", file=output)
    print_block(entity.income_statement, output, width=78, indent=-1,
                change_sign=True)
    print("\n\f", file=output)
    print_block(entity.assets, output, width=78, indent=-1)
    print("\n\f", file=output)
    print_block(entity.liabilities, output, width=78, indent=-1,
                change_sign=True)


def output_journal(entity, output):
    for tx in entity.transactions:
        print(f"{tx.id} {tx.date:%Y%m%d} {tx.description}", file=output)
        for entry in tx.entries:
            print(
                f"  {entry.account} {entry.change} {entry.description or ''}",
                file=output)
        print(file=output)


@click.command()
@click.argument('DIRECTORY', type=click.Path(dir_okay=True, file_okay=False))
@click.option('--output-directory', default="output", type=click.Path(dir_okay=True, file_okay=False, writable=True))
def main(directory, output_directory):
    """
    Reference command-line implementation of a Finnish double-entry
    bookkeeping utility.

    Input argument DIRECTORY should contain a directory of text files,
    one for each month, containing entries that contain a transaction number,
    description, and account entries that add up to zero.  The text files
    should be named with the template "YYYY-MM.txt", "YYYY" for the year and
    "MM" for the month.

    Output is written to directory "output" by default.
    """

    transactions = []
    input_files = list(
        filter(lambda ent: re.match("(data-)?[0-9]+-[0-9]+(\.txt)?$",
                                    ent.name),
               [entry for entry in pathlib.Path(directory).iterdir()
                if entry.is_file()]))

    if not input_files:
        raise click.ClickException(f"No input files found in {directory}.")

    num_files = len(input_files)
    print(f"Reading transactions from {num_files} file{'s' if num_files != 1 else ''}...")

    for entry in input_files:
        try:
            transactions.extend(txparser.parse(open(entry)))
        except txparser.InvalidInputError as e:
            if e.transaction_id is not None:
                tx = f"TX {e.transaction_id}: "
            else:
                tx = ""
            raise click.ClickException(f"{entry}: line {e.line}, col {e.column}:{tx} {str(e)}") from None

    defs_path = os.path.join(directory, "ledger-defs.txt")
    if os.path.exists(defs_path):
        entity = defparser.parse(open(defs_path))
        entity.add_transactions(transactions)
    else:
        print("No ledger-defs.txt, deducing from transactions...")
        entity = ledger.Entity.create_from_transactions(transactions)

    output_directory = os.path.realpath(output_directory)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_general_ledger(entity,
                          open(os.path.join(output_directory,
                                            "general-ledger.txt"), "w"))

    output_statement(entity,
                     open(os.path.join(output_directory,
                                       "statement.txt"), "w"))

    output_journal(entity,
                   open(os.path.join(output_directory,
                                     "journal.txt"), "w"))

    print(f"Output left in directory {output_directory}.")


if __name__ == "__main__":
    main()
