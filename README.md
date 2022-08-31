# POLARIS CRYPTO BOT - FRAMEWORK
## ABOUT THIS PROJECT
Polaris is a crypto bot framework that aims to
abroad every essential step of a semi-automatic
trading routine with crypto actives.

Coded almost completely in Python 3.8. 1?

- Capture trading data via API from the broker (binance.com).
- Parse data (klines) and dates.
- Store data in a pre-configured mongo database. NoSQL.
- Enable functions to continuously accessing data for analytics purpose.
- Integration with the framework Backtrader (Backtrader repo info here).
    Visualization, backtest, optimizations.
- Schedule periodically data capture.
- Manage personal account via api.
- Apply portfolio creation and rebalancing.
- Live Algoritmic trading.
- Notebooks for analysis and visualitazion.

## HOW TO USE
First at all is necessary an active Binance account and API permissions.
- Get some datasets.
- Choose some trading strategy and an apropiate account managment or perfil.
- Test and optimize parametros.
- Run live trading in a funded account.
- Continuously check your trading rules and bot permorfance.

## INSTALL
Clone this repo or run the Docker container... SOON.

## CONFIG FILES
pass

## Annotations
- Recomended, after all: pip install -r requirements.txt

>cd /home/llagask/Trading/polaris_beta/src/polaris-tools && pip install -e .