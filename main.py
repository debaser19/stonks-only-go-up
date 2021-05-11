import streamlit as st
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import config
import ast
import plotly.express as px
import plotly.graph_objects as go


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

    # need to return the string representation of a list as a list
    return ast.literal_eval(positions)


def main():
    st.title("Tendies")
    st.dataframe(get_current_balances())
    chart_data = get_balance_history()
    chart_data['Date'] = chart_data.index
    # chart_data.index = chart_data.index.tz_convert('US/Eastern')

    # go
    data =[
        go.Scatter(
            y = chart_data.NetLiq,
            x = chart_data.Date,
            mode = 'lines',
            line = {'color': 'yellow'}
        )
    ]

    layout = go.Layout(
        uirevision = data,
        paper_bgcolor = 'rgb(14, 17, 23)',
        plot_bgcolor = 'rgb(14, 17, 23)',
        font = {'color': 'white'},
        hovermode = 'x'
    )

    fig = go.Figure(data=data, layout=layout)

    fig.update_xaxes(
        tickformat = '%I:%M %p\n%x',
        rangebreaks = [
            dict(bounds = ['sat', 'mon']),
            dict(bounds = [20, 4], pattern = 'hour')
        ]
    )

    #px
    # fig = px.line(chart_data, x = 'Date', y = 'NetLiq')
    # fig.update_xaxes(
    #     tickformat = '%I:%M %p\n%x',
    #     rangebreaks = [
    #         dict(bounds = ['sat', 'mon']),
    #         dict(bounds = [20, 4], pattern = 'hour')
    #     ]
    # )

    st.plotly_chart(fig, use_container_width=True)
    st.table(get_current_positions())
    print(chart_data)


if __name__ == '__main__':
    main()