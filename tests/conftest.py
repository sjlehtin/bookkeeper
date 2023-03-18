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
        SummaryLine "pakko oli laittaa";
      }
      Liabilities {

        Title "VASTATTAVAA";
        Group "Oma pääoma" {
            Account "2375" "Edellisen tilikauden käsittelemätön tulos";
            FiscalYearProfit "Tilikauden tulos" "2375";
            }
        SummaryLine "pakko oli laittaa";
      }
      }
      """
