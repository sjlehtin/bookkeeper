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


trspace = ''.maketrans('.,',', ')
trpoint = ''.maketrans('.,',',.')

def dformat_point(value):
    return '{:>,}'.format(value).translate(trpoint)

def dformat_comma(value):
    return '{:>,}'.format(value)

def dformat_space(value):
    return '{:>,}'.format(value).translate(trspace)

def dformat_plain(value):
    return str(value)

dformats = {
    'plain': dformat_plain,
    'space': dformat_space,
    'comma': dformat_comma,
    'point': dformat_point,
    }

dformat = dformat_plain

def set_numeric_format(numeric_format):
    global dformat
    dformat = dformats.get(numeric_format)
    if not dformat:
        raise Exception('Illegal numeric format "{}"'.format(numeric_format))

def output_general_ledger(ledger, output):
    for account in sorted(ledger.accounts.values(),
                          key=lambda acc: acc.number):
        if not account.entries:
            continue

        print("{:4} {}".format(account.number,account.name), file=output)
        cumulative = 0
        for entry in account.entries:
            cumulative += entry.change

            description = entry.description or entry.transaction.description
            if len(description) > 39:
                description = description[:36] + "..."

            print("{:>6} {:39} {} {:>10} {:>10}".
                      format(entry.transaction.id,description,entry.transaction.date,dformat(entry.change),dformat(cumulative)),
                      file=output)
        sep = "========="
        print("{:>79}".format(sep), file=output)
        print("{:>79}".format(dformat(account.balance)), file=output)


def output_statement(entity, output):
    def print_block(block, out, indent=0, width=68, change_sign=False):
        if block.sum() == 0:
            return

        given_indent = indent
        indent = given_indent if given_indent > 0 else 0
        ind = " " * 2 * indent

        print("{}{}".format(ind,block.title), file=out)

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
                    "{}{:{}} {:>10}".format(ind,member.summary,summary_width,dformat(multiplier * acc)),
                    file=out)
            else:
                assert (isinstance(member, ledger.Account) or
                        isinstance(member, ledger.Profit)), \
                    "Unexcepted type, got {}".format(type(member))
                if member.sum() != 0:
                    print(
                        "{}  {:{}} {:>10}".format(ind,member.description(),name_width,dformat(multiplier * member.sum()),),
                        file=out)
        print(
            "{}{:{}} {:>10}".format(ind,block.summary,summary_width,dformat(multiplier * block.sum())),
            file=out)

    print("{}   {} - {}\n".format(entity.name,entity.fiscal_year_start,entity.fiscal_year_end), file=output)
    print_block(entity.income_statement, output, width=78, indent=-1,
                change_sign=True)
    print("\n\f", file=output)
    print_block(entity.assets, output, width=78, indent=-1)
    print("\n\f", file=output)
    print_block(entity.liabilities, output, width=78, indent=-1,
                change_sign=True)


def output_journal(entity, output):
    for tx in entity.transactions:
        print("{} {:%Y%m%d} {}".format(tx.id,tx.date,tx.description), file=output)
        for entry in tx.entries:
            print(
                "  {} {} {}".format(entry.account,entry.change,entry.description or ''),
                file=output)
        print(file=output)


@click.command()
@click.argument('DIRECTORY', type=click.Path(dir_okay=True, file_okay=False))
@click.option('--output-directory', default="output", type=click.Path(dir_okay=True, file_okay=False, writable=True))
@click.option('--numeric-format', default="plain")
def main(directory, output_directory, numeric_format):
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

    set_numeric_format(numeric_format)

    transactions = []
    input_files = list(
        filter(lambda ent: re.match("(data-)?[0-9]+-[0-9]+(\.txt)?$",
                                    ent.name),
               [entry for entry in pathlib.Path(directory).iterdir()
                if entry.is_file()]))

    if not input_files:
        raise click.ClickException("No input files found in current working "
                                   "directory.")

    print("Reading transactions from {} files...".format(len(input_files)))

    for entry in input_files:
        try:
            transactions.extend(txparser.parse(open(entry)))
        except txparser.InvalidInputError as e:
            if e.transaction_id is not None:
                tx = "TX {}: ".format(e.transaction_id)
            else:
                tx = ""
            raise click.ClickException("{}:{}[{}]:{} {}".format(entry,e.line,e.column,tx,str(e))) from None

    defs_path = os.path.join(directory, "ledger-defs.txt")
    if os.path.exists(defs_path):
        entity = defparser.parse(open(defs_path))
        entity.add_transactions(transactions)
    else:
        print("No ledger-defs.txt, deducing from transactions...")
        entity = ledger.Entity.create_from_transactions(transactions)

    output_directory = os.path.realpath(output_directory)
    print("Writing output to {}...".format(output_directory))

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


if __name__ == "__main__":
    main()
