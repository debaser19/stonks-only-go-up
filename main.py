import streamlit as st
from influxdb import DataFrameClient
import pandas as pd
import config
import ast
import plotly.graph_objects as go
import pattern_recognition


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
        return df
    except KeyError as e:
        st.write(f'No plot points in selected timeframe: {timeframe}')
        st.write(e)


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
    option_positions = get_current_positions('Options')
    option_tickers = [t['ticker'].split('_')[0] for t in option_positions]

    stock_positions = get_current_positions('Positions')
    stock_tickers = [t['ticker'] for t in stock_positions]

    return list(set(option_tickers) | set(stock_tickers))
    

def get_portfolio_percentages():
    option_positions = get_current_positions('Options')
    option_tickers = [t['description'] for t in option_positions]
    option_value = [t['pos_net_liq'] for t in option_positions]

    option_data = [
        go.Pie(
            labels=option_tickers,
            values=option_value,
            textinfo='label+percent'
        )
    ]

    stock_positions = get_current_positions('Positions')
    stock_tickers = [t['ticker'] for t in stock_positions]
    stock_value = [v['pos_net_liq'] for v in stock_positions]
    
    stock_data = [
        go.Pie(
            labels=stock_tickers,
            values=stock_value,
            textinfo='label+percent'
        )
    ]

    return go.Figure(stock_data), go.Figure(option_data)


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


def create_table(positions):
    pos_df = pd.DataFrame(positions)
    pos_df.set_index('ticker', inplace=True)
    pos_df.index.name = 'Ticker'

    return pos_df


def main():
    watchlist = ['DKNG', 'NET', 'TSLA', 'GM', 'ABNB', 'GNOG', 'SPY', 'RKT', 'NVDA', 'SQ', 'FMAC',
                 'IPOF', 'PLUG', 'AMD', 'AAPL', 'BB', 'TSM', 'WKHS', 'NIO', 'PLTR', 'GME', 'AMC',
                 'TLRY', 'SNAP', 'ALLY', 'MSFT', 'ATVI', 'PENN', 'INTC', 'AMZN', 'COST', 'ARKK',
                 'U', 'TWTR', 'ROKU', 'BAC', 'X', 'F']

    st.set_page_config(layout="wide") 
    # sidebar
    st.sidebar.header("Timeframe Selection")
    pos_slider = st.sidebar.select_slider(
        'Select a timeframe',
        options=["1h", "2h", "3h", "6h", "12h", "24h", "7d", "30d"]
    )

    st.sidebar.header("Ticker List")
    symbol = st.sidebar.selectbox('Current Watchlist', watchlist)

    # Pattern Recognition
    pattern_timeframe = st.sidebar.select_slider(
        'Select Pattern Recognition Timeframe',
        options=range(1, 366)
    )
    st.sidebar.header("Pattern Recognition")
    st.sidebar.write(f"{symbol} Morning Star Candles")
    st.sidebar.dataframe(pattern_recognition.morning_star_candle(symbol, pattern_timeframe))

    st.sidebar.write(f"{symbol} Engulfing Candles")
    st.sidebar.dataframe(pattern_recognition.engulfing_candle(symbol, pattern_timeframe))

    # main section
    st.title("Tendies")
    # st.dataframe(get_current_balances())
    st.write(get_current_balances())

    # port graph
    st.plotly_chart(create_graph(pos_slider), use_container_width=True)

    # set up cols
    col1, col2 = st.beta_columns(2)

    col1.header("Stonks")
    # stock pie chart
    with col1:
        st.plotly_chart(get_portfolio_percentages()[0])

    col2.header("Options")
    # option pie chart
    with col2:
        st.plotly_chart(get_portfolio_percentages()[1])
    
    # positions
    st.header('Stonks')
    st.table(create_table(get_current_positions('Positions')))
    # st.table(get_current_positions('Positions'))

    st.header('Options')
    st.table(create_table(get_current_positions('Options')))
    # st.table(get_current_positions('Options'))


if __name__ == '__main__':
    main()
