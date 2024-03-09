import pytest


@pytest.fixture
def simple_ledger_def():
    return """Entity "Semeai Oy" {
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
      Group "Rahat ja pankkisaamiset" {
	Account "1910" "Pankkitili";
}    

        SummaryLine "pakko oli laittaa";
      }
      Liabilities {

        Title "VASTATTAVAA";
        
        Group "Oma pääoma" {
          Account "2001" "Osakepääoma";
        Account "2375" "Edellisen tilikauden käsittelemätön tulos";
            FiscalYearProfit "Tilikauden tulos" "2375";
            }
        SummaryLine "pakko oli laittaa";
      }
      }
      """


@pytest.fixture
def simple_tx_data():
    return """\
0 20120203 Ei avaavaa tasetta, yhtiö perustettu

1 20120203 Osakepääoma/Perustaja 1
  1910 1250.00
  2001 -1250.00

2 20120203 Osakepääoma/Perustaja 2
  1910 1250.00
  2001 -1250.00
"""


@pytest.fixture
def no_transactions_directory(tmp_path, simple_ledger_def):
    with open(tmp_path / "ledger-defs.txt", "w") as fp:
        fp.write(simple_ledger_def)
    return tmp_path


@pytest.fixture
def simple_input_directory(no_transactions_directory, simple_tx_data):
    with open(no_transactions_directory / "data-2012-01.txt", "w") as fp:
        fp.write(simple_tx_data)

    return no_transactions_directory
