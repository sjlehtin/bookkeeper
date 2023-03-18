from bookkeeper import defparser
from bookkeeper.main import output_statement
from io import StringIO


def test_ledger_output_with_no_transactions(simple_ledger_def):
    def_string = simple_ledger_def
    entity = defparser.parse(StringIO(def_string))

    entity.add_transactions([])

    output_file = StringIO()

    output_statement(entity, output_file)
