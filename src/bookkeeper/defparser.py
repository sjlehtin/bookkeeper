from lark import Lark, UnexpectedInput, ParseError
from .ledger import InvalidInputError, Entity, Account, Block, Profit, \
    SummaryLine
import re
import datetime
import itertools


grammar = r"""
start: entity?

%import common.NEWLINE
%import common.WS_INLINE
%import common.WS
%import common.ESCAPED_STRING

COMMENT :  "/*" /.+/ "*/"

%ignore COMMENT 

_ALLWS: WS
_WS: WS_INLINE
_NL: NEWLINE

%import common.DIGIT

date: YEAR "-" MONTH "-" DAY
YEAR: DIGIT DIGIT DIGIT DIGIT
MONTH: DIGIT DIGIT
DAY: DIGIT DIGIT

ACCOUNT: DIGIT+ 
account: "Account" "\"" ACCOUNT "\""  NAME ";"

NAME: ESCAPED_STRING

title: "Title" NAME ";"

DESCRIPTION: ESCAPED_STRING

profit: "FiscalYearProfit" DESCRIPTION "\"" ACCOUNT "\"" ";"
group: "Group" DESCRIPTION "{" (account|profit|group)* "}"
summary: "SummaryLine" DESCRIPTION ";"
fiscal_year: "CurrentFiscalYear" date date ";"
block: title (group|summary)* summary
income: "IncomeStatement" "{" block "}"
assets: "Assets" "{" block "}"
liabilities: "Liabilities" "{" block "}"

entity: "Entity" NAME "{" fiscal_year income assets liabilities "}"

%ignore WS 
"""
parser = Lark(grammar)


def parse_account(node):
    assert node.data == "account"
    return Account(int(node.children[0]), unescape(node.children[1]))


def parse_profit(node):
    assert node.data == "profit"
    return Profit(int(node.children[1]), unescape(node.children[0]))


def parse_group(node):
    members = []

    title = unescape(node.children[0])
    for cc in node.children[1:]:
        if cc.data == "account":
            members.append(parse_account(cc))
        elif cc.data == "profit":
            members.append(parse_profit(cc))
        else:
            assert cc.data == "group", \
                f"Expected group, got {cc.data}"
            members.append(parse_group(cc))

    return Block(members, title=title, summary="  " + title)


def parse_summary_line(node):
    return SummaryLine(unescape(node.children[0]))


def parse_block(node):
    if len(node.children) != 1:
        raise ValueError("Invalid block")

    content = node.children[0]
    if content.data != "block":
        raise ValueError(f"Expected block, got {content.data}")

    title = content.children[0]
    assert title.data == "title"
    title = unescape(title.children[0])

    members = []

    for member in content.children[1:-1]:
        if member.data == "summary":
            members.append(parse_summary_line(member))
        else:
            assert member.data == "group", \
                f"Invalid top-level member {member.data}"
            members.append(parse_group(member))

    summary = content.children[-1]
    assert summary.data == "summary"
    summary = unescape(summary.children[0])

    return Block(members, title, summary)


def parse_blocks(nodes):
    if len(nodes) != 3:
        raise ValueError("Invalid parse")

    income = nodes[0]
    assets = nodes[1]
    liabilities = nodes[2]

    return parse_block(income), parse_block(assets), parse_block(liabilities)


def unescape(name):
    # get rid of quotes in the beginning and end.
    name = name[1:-1]
    repls = [(r"\\\"", r'"'), (r"\\n", '\n')]
    for repl in repls:
        name = re.sub(repl[0], repl[1], name)
    return name


def normalize(number):
    new = ''.join(itertools.dropwhile(lambda xx: xx == "0", number))
    if not new:
        new = 0
    return int(new)


def parse_fiscal_year(given_fiscal_year):
    year = normalize(given_fiscal_year.children[0])
    month = normalize(given_fiscal_year.children[1])
    day = normalize(given_fiscal_year.children[2])
    fiscal_year = datetime.date(year=year, month=month, day=day)
    return fiscal_year


def parse(def_file):
    """
    Parse the given file `def_file`.
    """
    try:
        tree = parser.parse(def_file.read())
    except UnexpectedInput as exc:
        raise InvalidInputError(str(exc), getattr(def_file, 'name', None),
                                exc.line, exc.column)
    except ParseError as exc:
        raise InvalidInputError(str(exc), getattr(def_file, 'name', None))

    if not tree.children:
        return

    entity = tree.children[0]
    entity_name = entity.children[0]

    entity_fiscal_year = entity.children[1]
    fiscal_year_start = entity_fiscal_year.children[0]
    fiscal_year_end = entity_fiscal_year.children[1]

    top_level = parse_blocks(entity.children[2:])
    accounts = list(Block.find(top_level, Account))
    income_statement, assets, liabilities = top_level

    accounts.sort(key=lambda acc: acc.number)

    dikt = {}
    for acc in accounts:
        if acc.number in dikt:
            raise InvalidInputError(f"Account {acc.number} defined "
                                    f"multiple times")
        dikt[acc.number] = acc

    return Entity(unescape(entity_name), dikt,
                  income_statement=income_statement,
                  assets=assets,
                  liabilities=liabilities,
                  fiscal_year_start=parse_fiscal_year(fiscal_year_start),
                  fiscal_year_end=parse_fiscal_year(fiscal_year_end))
