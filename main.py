import streamlit as st
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import config
import ast


def connect_to_api():
    pass


def get_balance_history():
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, NetLiq from balance where time > now() - 1d'
    results = client.query(query)
    df = pd.DataFrame(results['balance'])
    df['NetLiq'] = pd.to_numeric(df['NetLiq'], downcast='float')

    return df
    # return results['balance']


def get_current_balances():
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select time, BuyingPower, Cash, MarginBalance, NetLiq from balance group by * order by time desc limit 1'
    results = client.query(query)

    return results['balance']


def get_current_positions():
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select time, Positions from balance group by * order by time desc limit 1'
    results = client.query(query)
    
    positions = results['balance'].iloc[0]['Positions']

    return ast.literal_eval(positions)


def main():
    st.title("Tendies")
    st.dataframe(get_current_balances())
    chart_data = get_balance_history()
    # chart_data.index = chart_data.index.tz_convert('US/Eastern')
    st.line_chart(chart_data)
    st.table(get_current_positions())
    print(chart_data)


if __name__ == '__main__':
    main()