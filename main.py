from tda import auth, client
from flask import render_template
# import Flask
import json
import config


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


def getNetLiq():
    return getAccountInfo()['securitiesAccount']['initialBalances']['liquidationValue']


if __name__ == '__main__':
    print(json.dumps(getAccountInfo(), indent=4))