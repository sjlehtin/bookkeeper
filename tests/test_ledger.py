from bookkeeper import ledger, txparser, defparser
import io
import pytest


def test_ledger():
    txs = txparser.parse(io.StringIO("""0 20180301 foo
  45 -100.00
  65 100.00  Zappadai zupaduu

1 20180302 bar
  50 -100.00
  65 100.00  Zappadai zupaduu

"""))
    main = ledger.Entity.create_from_transactions(txs)
    assert main.accounts[45].balance == -100
    assert main.accounts[45].name == "auto"
    assert main.accounts[45].number == 45
    assert main.accounts[50].balance == -100
    assert main.accounts[65].balance == 200
    assert main.accounts[65].number == 65
    assert len(main.transactions) == 2

    main = ledger.Entity.create_from_transactions(txparser.parse(io.StringIO("")))
    assert len(main.transactions) == 0


def test_ledger_with_entity():
    def_string = """Entity "Semeai Oy" {
        CurrentFiscalYear 2017-01-01 2017-12-31;
      IncomeStatement {
        Title "TULOSLASKELMA JA TASE";
    Group "Liikevaihto" {
      Account "3000" "Osto";
      Account "3001" "Myynti";
      }
      SummaryLine "Foofaafom";
      }
      Assets {        
        Title "VASTAAVAA";
        SummaryLine "pakko oli laittaa";
      }
      Liabilities {
        Title "VASTATTAVAA";
        SummaryLine "pakko oli laittaa";
      }
      }
      """
    entity = defparser.parse(io.StringIO(def_string))
    txs = txparser.parse(io.StringIO("""0 20180301 foo
  3000 -100.00
  3001 100.00  Zappadai zupaduu
"""))
    entity.add_transactions(txs)
    assert entity.accounts[3000].balance == -100

    txs = txparser.parse(io.StringIO("""0 20180301 foo
  45 -100.00
  3001 100.00  Zappadai zupaduu
"""))
    with pytest.raises(ledger.InvalidTransactionError) as exc_info:
        entity.add_transactions(txs)
    assert "no such account: 45" in str(exc_info.value)


def test_invalid_ledger():
    with pytest.raises(ledger.InvalidTransactionError) as exc_info:
        ledger.Entity.create_from_transactions(txparser.parse(io.StringIO(
            """0 20180301 foo
  45 -100.00
  65 100.00  Zappadai zupaduu

2 20180302 bar
  50 -100.00
  65 100.00  Zappadai zupaduu

""")))

    assert "Missing or extra transaction" in str(exc_info.value)


def test_ledger_with_groups():
    entity = defparser.parse(io.StringIO("""Entity "Semeai Oy" {
        CurrentFiscalYear 2017-01-01 2017-12-31;
      IncomeStatement {
        Title "TULOSLASKELMA JA TASE";
    Group "Liikevaihto" {
      Account "3000" "Osto";
      Account "3001" "Myynti";
      Group "Jatsi" {
        Account "4000" "Tatsi";
      }
      }
      SummaryLine "Foofaafom";
      }
      Assets {
        Title "VASTAAVAA";
          Group "Jatsi" {
            Account "8000" "Satsi";
          }
        SummaryLine "pakko oli laittaa";
      }
      Liabilities {
      Title "KOVASTI PALJON VASTATTAVAA";
      Group "Tsappadai" {
        Account "5000" "Tsunktsunk";
        FiscalYearProfit "Tulosta pitäis" "0000";
      }
      SummaryLine "Hui kauhia";
      }
      }
      """))

    txs = txparser.parse(io.StringIO("""0 20180301 foo
  3000 -100.00
  3001 100.00  Zappadai zupaduu

1 20180302 bar
  4000 250.00  Puppup
  5000 -250.00 Tsappap

3 20180304 Pofpof
  5000 300.00    Tsupadui
  8000 -300.00   Tsapadai

2 20180303 zappa
  3001 170.00  Luplup
  5000 -170.00 Gupgup
  
"""))
    entity.add_transactions(txs)
    main = entity

    assert main.accounts[4000].balance == 250
    assert entity.accounts[4000].balance == 250
    assert entity.income_statement.sum() == 420
    assert entity.liabilities.sum() == 300
    assert entity.assets.sum() == -300

    assert [0, 1, 2, 3] == [tx.id for tx in entity.transactions]