import streamlit as st
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import config
import ast
import plotly.express as px
import plotly.graph_objects as go


def connect_to_api():
    pass


def get_balance_history(timeframe):
    tz_offset = 4
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, NetLiq from balance where time > now() - {tz_offset}h - {timeframe}'
    results = client.query(query)
    try:
        df = pd.DataFrame(results['balance'])
        df['NetLiq'] = pd.to_numeric(df['NetLiq'], downcast='float')
    except KeyError as e:
        st.write(f'No plot points in selected timeframe: {timeframe}')
        st.write(e)

    return df
    # return results['balance']


def get_current_balances():
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select time, BuyingPower, Cash, MarginBalance, NetLiq from balance group by * order by time desc limit 1'
    results = client.query(query)

    return results['balance']


def get_current_positions(position):
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, {position} from balance group by * order by time desc limit 1'
    results = client.query(query)
    
    positions = results['balance'].iloc[0][position]

    # need to return the string representation of a list as a list
    return ast.literal_eval(positions)


def get_ticker_list():
    positions = get_current_positions('Positions')
    
    return positions


def get_portfolio_percentages():
    positions = get_current_positions('Positions')

    tickers = [t['ticker'] for t in positions]
    value = [v['pos_net_liq'] for v in positions]
    
    data = [
        go.Pie(
            labels = tickers,
             values = value,
             textinfo = 'label+percent'
        )
    ]

    return go.Figure(data)


def create_graph(pos_slider):
    chart_data = get_balance_history(pos_slider)
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

    return fig


def main():
    pos_slider = st.sidebar.select_slider(
        'Select a timeframe',
        options = ["1h", "2h", "3h", "6h", "12h", "24h", "7d", "30d"])
    st.title("Tendies")
    st.dataframe(get_current_balances())

    # port graph
    st.plotly_chart(create_graph(pos_slider), use_container_width=True)

    # port pie chart
    st.plotly_chart(get_portfolio_percentages())

    # TODO: convert tables to plotly tables
    # positions
    st.write('Stocks')
    st.table(get_current_positions('Positions'))
    st.write('Options')
    st.table(get_current_positions('Options'))


if __name__ == '__main__':
    main()