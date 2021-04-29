from tda import auth, client
import json
import config
import datetime
from influxdb import InfluxDBClient
import ast


api_key = config.api_key
token_path = config.balance_token_path
redirect_uri = config.redirect_uri


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
            return c


def getAccountInfo():
    c = connectToApi()
    r = c.get_account(config.account_number, fields=c.Account.Fields.POSITIONS)
    account_info = r.json()

    return account_info


# def getBalances():
#     balance_dict = {
#         'net_liq': account_info['securitiesAccount']['currentBalances']['liquidationValue'],
#         'cash': account_info['securitiesAccount']['currentBalances']['availableFunds'],
#         'buying_power': account_info['securitiesAccount']['currentBalances']['buyingPower'],
#         'margin_balance': account_info['securitiesAccount']['currentBalances']['marginBalance']
#     }

#     return balance_dict


def get_positions():
    # account_info = getAccountInfo()
    stock_positions = []
    option_positions = []
    positions_list = account_info['securitiesAccount']['positions']
    
    for position in positions_list:

        long_quantity = position['longQuantity']
        short_quantity = position['shortQuantity']
        quantity = long_quantity - short_quantity
        trade_price = position['averagePrice']
        current_price = abs(position['marketValue']) / abs(long_quantity - short_quantity)
        pl_day = position['currentDayProfitLoss']
        pl_day_percent = position['currentDayProfitLossPercentage']
        ticker = position['instrument']['symbol']


        if quantity > 0:
            # long position
            pl_open = ((current_price - trade_price) * abs(quantity))
        else:
            # short position
            pl_open = ((trade_price - current_price) * abs(quantity))

        # check the asset type
        if position['instrument']['assetType'] == 'EQUITY': # asset type is shares

            stock_position_dict = {
                'asset_type': position['instrument']['assetType'],
                'ticker': ticker,
                'quantity': quantity,
                'trade_price': f'{trade_price:.2f}',
                'current_price': f'{current_price:.2f}',
                'pos_net_liq': f'{position["marketValue"]:.2f}',
                'pl_day': f'{pl_day:.2f}',
                'pl_day_percent': f'{pl_day_percent:.2f}',
                'pl_open': f'{pl_open:.2f}'
            }

            stock_positions.append(stock_position_dict)


        # asset type is an option, determine if call/put
        if position['instrument']['assetType'] == 'OPTION':
            if quantity > 0:
                # long position
                pl_open = (((current_price) / 100 - trade_price) * abs(quantity)) * 100
            else:
                # short position
                pl_open = ((trade_price - (current_price) / 100) * abs(quantity)) * 100

            option_position_dict = {
                'asset_type': position['instrument']['putCall'],
                'ticker': position['instrument']['symbol'],
                'description': position['instrument']['description'],
                'quantity': quantity,
                'trade_price': f'{trade_price:.2f}',
                'current_price': f'{current_price / 100:.2f}',
                'pos_net_liq': f'{position["marketValue"]:.2f}',
                'pl_day': f'{pl_day:.2f}',
                'pl_day_percent': f'{pl_day_percent:.2f}',
                'pl_open': f'{pl_open:.2f}'
            }

            option_positions.append(option_position_dict)

    balance_dict = {
        'net_liq': f"{account_info['securitiesAccount']['currentBalances']['liquidationValue']:,}",
        'cash': f"{account_info['securitiesAccount']['currentBalances']['availableFunds']:,}",
        'buying_power': f"{account_info['securitiesAccount']['currentBalances']['buyingPower']:,}",
        'margin_balance': f"{account_info['securitiesAccount']['currentBalances']['marginBalance']:,}"
    }
    
    return stock_positions, option_positions, balance_dict


if __name__ == '__main__':
    account_info = getAccountInfo()
    the_goods = get_positions()
    now = datetime.datetime.now()

    json_body = [
        {
            'measurement': 'balance',
            'time': now,
            'fields': {
                'NetLiq': the_goods[2]['net_liq'].replace(',', ''),
                'Cash': the_goods[2]['cash'],
                'MarginBalance': the_goods[2]['margin_balance'],
                'BuyingPower': the_goods[2]['buying_power'],
                'Positions': str(the_goods[0])
            }
        }
    ]
    
    client = InfluxDBClient('localhost', 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    client.create_database('balance_history')
    client.write_points(json_body)

    result = client.query('select * from balance;')
    print(f'Logging result: {now} - {the_goods[2]["net_liq"]}')
