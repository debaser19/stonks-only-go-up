from tda import auth, client
import json
import config
import datetime
from influxdb import InfluxDBClient


api_key = config.api_key
token_path = config.token_path
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


if __name__ == '__main__':
    balance = getBalances()['net_liq']
    now = datetime.datetime.now()

    json_body = [
        {
            'measurement': 'balance',
            'time': now,
            'fields': {
                'value': balance
            }
        }
    ]
    
    client = InfluxDBClient('localhost', 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    client.create_database('balance_history')
    client.write_points(json_body)

    result = client.query('select * from balance;')
    print(f'Logging result: {now} - {balance}')
