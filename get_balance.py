import creds
import os
from selenium import webdriver
import time
import sqlite3
import datetime


def get_account_balance():
    if os.name == 'nt':     # if windows
        driver_path = '.\\driver\\chromedriver.exe'
    else:   # if osx/linux
        driver_path = './driver/chromedriver'

    # set driver, open and navigate to login
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.get('https://manage.tastyworks.com/index.html#/login')

    # enter login
    tw_user_field = driver.find_element_by_id('ember881')
    tw_user_field.send_keys(creds.creds['tw_user'])

    # enter password
    tw_pass_field = driver.find_element_by_id('ember883')
    tw_pass_field.send_keys(creds.creds['tw_pass'])

    # click the login button
    driver.find_element_by_class_name('login-button').click()

    # navigate to balances
    driver.get('https://manage.tastyworks.com/index.html#/accounts/balances')

    # give a few seconds to let page load
    time.sleep(3)

    # get account balance
    balance = driver.find_element_by_class_name('balance').text
    # drop the $ from string
    balance = balance[1:]

    # return the balance string as a float without commas
    return float(balance.replace(',', ''))


def write_db():
    # set parameters to use as insertion values
    params = (datetime.datetime.now(), current_balance)
    # connect to the db, create if it does not exist
    conn = sqlite3.connect('database/balance_db.db')
    c = conn.cursor()

    # create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS balance
    (timestamp datetime, balance real)''')

    # write balance to db
    c.execute('INSERT INTO balance VALUES (?, ?)', params)

    # commit to db
    conn.commit()
    conn.close()


if __name__ == '__main__':
    current_balance = get_account_balance()
    write_db()
