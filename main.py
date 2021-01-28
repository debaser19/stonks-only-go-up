from tda import auth, client
from flask import Flask, render_template
import json
import config


api_key = config.api_key
token_path = config.token_path
redirect_uri = config.redirect_uri

app = Flask(__name__)


def connectToApi():
    # generate token
    try:
        c = auth.client_from_token_file(token_path, api_key)
        return c
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(
                driver, api_key, redirect_uri, token_path)


def getAccountInfo():
    c = connectToApi()
    r = c.get_account('455720137', fields=c.Account.Fields.POSITIONS)
    account_info = r.json()

    return account_info


def getBalances():
    account_info = getAccountInfo()
    balance_dict = {
        'net_liq': account_info['securitiesAccount']['currentBalances']['liquidationValue'],
        'cash': account_info['securitiesAccount']['currentBalances']['availableFunds'],
        'buying_power': account_info['securitiesAccount']['currentBalances']['buyingPower'],
        'margin_balance': account_info['securitiesAccount']['currentBalances']['marginBalance']
    }

    return balance_dict


@app.route('/')
def index():
    account_info = getAccountInfo()

    # account balances
    balance_dict = {
        'net_liq': account_info['securitiesAccount']['currentBalances']['liquidationValue'],
        'cash': account_info['securitiesAccount']['currentBalances']['availableFunds'],
        'buying_power': account_info['securitiesAccount']['currentBalances']['buyingPower'],
        'margin_balance': account_info['securitiesAccount']['currentBalances']['marginBalance']
    }

    print(balance_dict)

    # positions
    # create empty lists for stocks and options
    stock_positions = []
    option_positions = []
    positions_list = account_info['securitiesAccount']['positions']
    
    for position in positions_list:

        # check the asset type
        if position['instrument']['assetType'] == 'EQUITY': # asset type is shares

            stock_position_dict = {
                'asset_type': position['instrument']['assetType'],
                'ticker': position['instrument']['symbol'],
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'trade_price': position['averagePrice'],
                'current_price': 'fixme',
                'pl_day': position['currentDayProfitLoss'],
                'pl_day_percent': position['currentDayProfitLossPercentage'],
                'pl_open': 'fixme'
            }

            stock_positions.append(stock_position_dict)

        # asset type is an option, determine if cal/put
        else:

            option_position_dict = {
                'asset_type': position['instrument']['putCall'],
                'ticker': position['instrument']['underlyingSymbol'],
                'description': position['instrument']['description'],
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'trade_price': position['averagePrice'],
                'current_price': 'fixme',
                'pl_day': position['currentDayProfitLoss'],
                'pl_day_percent': position['currentDayProfitLossPercentage'],
                'pl_open': 'fixme'
            }

            option_positions.append(option_position_dict)
    
    return render_template('index.html',
    balance_dict=balance_dict,
    stock_positions=stock_positions,
    option_positions=option_positions)


if __name__ == '__main__':
    app.run(debug=True)