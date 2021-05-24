import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from influxdb import DataFrameClient
import config


def get_balance_history(timeframe):
    tz_offset = 4
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, NetLiq from balance where time > now() - {tz_offset}h - {timeframe}'
    results = client.query(query)
    try:
        df = pd.DataFrame(results['balance'])
        df['NetLiq'] = pd.to_numeric(df['NetLiq'], downcast='float')
        return df
    except KeyError as e:
        st.write(f'No plot points in selected timeframe: {timeframe}')
        st.write(e)


def get_current_balances():
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select time, BuyingPower, Cash, MarginBalance, NetLiq from balance group by * order by time desc limit 1'
    results = client.query(query)

    return results['balance']


def create_graph(pos_slider):
    chart_data = get_balance_history(pos_slider)
    chart_data['Date'] = chart_data.index
    
    # check if red or green
    if chart_data.NetLiq.iloc[0] < chart_data.NetLiq.iloc[-1]:
        line_color = 'lightgreen'
    elif chart_data.NetLiq.iloc[0] > chart_data.NetLiq.iloc[-1]:
        line_color = 'red'
    else:
        line_color = 'yellow'

    # plotly go
    data = [
        go.Scatter(
            y=chart_data.NetLiq,
            x=chart_data.Date,
            mode='lines',
            line={'color': f'{line_color}'}
        )
    ]

    layout = go.Layout(
        uirevision=data,
        paper_bgcolor='rgb(14, 17, 23)',
        plot_bgcolor='rgb(14, 17, 23)',
        font={'color': 'white'},
        hovermode='x'
    )

    fig = go.Figure(data=data, layout=layout)

    fig.update_xaxes(
        tickformat='%I:%M %p\n%x',
        rangebreaks=[
            dict(bounds=['sat', 'mon']),
            dict(bounds=[20, 4], pattern='hour')
        ]
    )

    return fig


def display_pl_graph():
    st.sidebar.header("P/L Graph Timeframe")
    pos_slider = st.sidebar.select_slider(
        'Select a timeframe',
        options=["1h", "2h", "3h", "6h", "12h", "24h", "7d", "30d", "45d", "60d"]
    )

    # main section
    st.title("Tendies")
    # st.dataframe(get_current_balances())
    st.write(get_current_balances())

    # port graph
    st.plotly_chart(create_graph(pos_slider), use_container_width=True)