from bookkeeper import defparser, ledger
import io
import pytest
import datetime


def test_defparser():
    entity = defparser.parse(io.StringIO(""))
    assert entity is None, "Empty file should be ok"

    entity = defparser.parse(io.StringIO("""Entity "Semeai Oy" {
    CurrentFiscalYear 2017-01-01 2018-03-01;
      IncomeStatement {        
        Title "TULOSLASKELMA JA TASE";
        SummaryLine "pakko oli laittaa";
      }
      Assets {        
        Title "VASTAAVAA";
        SummaryLine "pakko oli laittaa";
      }
      Liabilities {
        Title "VASTATTAVAA";
        SummaryLine "pakko oli laittaa";
      }    
    }"""))
    assert isinstance(entity, defparser.Entity)
    assert entity.fiscal_year_start == datetime.date(2017, 1, 1)
    assert entity.fiscal_year_end == datetime.date(2018, 3, 1)

    entity = defparser.parse(io.StringIO("""Entity "Semeai Oy" {
    CurrentFiscalYear 2017-01-01 2017-12-31;
    /* Account "9876" Foofoo;  */
        /* Comments should be ok. */
    
      IncomeStatement {        
        Title "TULOSLASKELMA JA TASE";
        SummaryLine "pakko oli laittaa";
      }
      Assets {        
        Title "VASTAAVAA";
        SummaryLine "pakko oli laittaa";
      }
      Liabilities {
        Title "VASTATTAVAA";
        SummaryLine "pakko oli laittaa";
      }    
    }"""))
    assert isinstance(entity, defparser.Entity)


    entity = defparser.parse(io.StringIO("""Entity "Semeai Oy" {
        CurrentFiscalYear 2017-01-01 2017-12-31;
      IncomeStatement {
        Title "TULOSLASKELMA JA TASE";
    Group "Liikevaihto" {
      Account "3001" "Myynti 23%";
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
          """))
    assert isinstance(entity, defparser.Entity)

    entity = defparser.parse(io.StringIO(r"""Entity "Semeai Oy" {
        CurrentFiscalYear 2017-01-01 2017-12-31;
      IncomeStatement {
        Title "TULOSLASKELMA JA TASE";
    Group "Liikevaihto" {
      Account "3001" "Myynti 23%";
      }
      SummaryLine "Foofaafom";

      Group "Rahat ja pankkisaamiset" {
	Account "1910" "\"Pankkitili";
      }
      SummaryLine "Tsappadai";
      SummaryLine "Tsuppadui";
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
          """))
    assert isinstance(entity, defparser.Entity)
    accounts = entity.get_accounts()
    assert len(accounts) == 2, "There are two accounts in test data"
    assert {1910, 3001} == {acc.number for acc in accounts}

    account = entity.accounts[1910]
    assert isinstance(account, ledger.Account)
    assert account.number == 1910, \
        "Accounts should be sorted according to number"
    assert account.name == "\"Pankkitili"
    assert entity.accounts[3001].name == "Myynti 23%"

    with pytest.raises(ledger.InvalidInputError) as exc_info:
        defparser.parse(io.StringIO(r"""Entity "Semeai Oy" {
  /* ReportingCurrency EUR; */

  /* FiscalYear 2013-01-01 2013-12-31; */
  /* FiscalYear 2014-01-01 2014-12-31; */
  /*CurrentFiscalYear 2015-01-01 2015-12-31;*/
CurrentFiscalYear 2017-01-01 2017-12-31;
  /* DefaultUnit "yleis" "Kohdistamattomat"; */
/*  Unit "j9esi" "TEKES J9 esitutkimusvaihe"; */


      IncomeStatement {
        Title "TULOSLASKELMA JA TASE";
    Group "Liikevaihto" {
      Account "3001" "Myynti 23%";
      }
      SummaryLine "Foofaafom";

      Group "Rahat ja pankkisaamiset" {
	Account "1910" "\"Pankkitili";
      }
      Group "Velat saataviksi" {
	Account "1910" "Toinen pankkitili";
      }
      SummaryLine "Tsappadai";
      SummaryLine "Tsuppadui";
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
          """))
    assert "1910 defined multiple times" in str(exc_info.value)


def test_normalize():
    assert 1 == defparser.normalize("01")
    assert 31 == defparser.normalize("31")
    assert 0 == defparser.normalize("0")
    assert 101 == defparser.normalize("0000101")


def test_entity():
    entity = defparser.parse(io.StringIO(r"""Entity "Semeai Oy" {
            CurrentFiscalYear 2017-01-01 2017-12-31;
          IncomeStatement {
            Title "TULOSLASKELMA JA TASE";
        Group "Liikevaihto" {
          Account "3001" "Myynti 23%";
          }
          SummaryLine "Foofaafom";

          Group "Rahat ja pankkisaamiset" {
    	Account "1910" "\"Pankkitili";
          }
          SummaryLine "Tsappadai\n";
          SummaryLine "VIIMEINEN RIVI";
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
              """))
    assert isinstance(entity.income_statement, ledger.Block)

    assert entity.income_statement.title == "TULOSLASKELMA JA TASE"
    assert entity.income_statement.summary == "VIIMEINEN RIVI"

    revenue = entity.income_statement.members[0]
    assert isinstance(revenue, ledger.Block)
    assert revenue.title == "Liikevaihto"
    assert revenue.summary == "  Liikevaihto"

    summaries = list(filter(lambda xx: isinstance(xx, ledger.SummaryLine),
                            entity.income_statement.members))
    assert len(summaries) == 2, "Last SummaryLine is for the enclosing block"
    assert summaries[0].summary == "Foofaafom"
    assert summaries[1].summary == """Tsappadai
"""


def test_account():
    acc = ledger.Account(3000, "foo")
    assert acc.description() == "3000 foo"


def test_profit():
    profit = ledger.Profit(3000, "Profit")
    assert profit.description() == "Profit"