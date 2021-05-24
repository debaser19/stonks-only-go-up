import talib
import yfinance as yf
import datetime
import plotly.graph_objects as go
import streamlit as st


def morning_star_candle(symbol, timeframe):
    today = datetime.datetime.today()
    days = datetime.timedelta(timeframe)

    start_date = (today - days).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    data = yf.download(symbol, start=start_date, end=end_date)

    morningstar = talib.CDLMORNINGSTAR(data['Open'], data['High'], data['Low'], data['Close'])

    return morningstar[morningstar != 0]


def engulfing_candle(symbol, timeframe):
    today = datetime.datetime.today()
    days = datetime.timedelta(timeframe)

    start_date = (today - days).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    data = yf.download(symbol, start=start_date, end=end_date)

    engulfing = talib.CDLENGULFING(data['Open'], data['High'], data['Low'], data['Close'])

    return engulfing[engulfing != 0]


def get_ohlc_data(symbol, timeframe):
    today = datetime.datetime.today()
    days = datetime.timedelta(timeframe)

    start_date = (today - days).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    return yf.download(symbol, start=start_date, end=end_date)


def create_candle_chart(symbol, timeframe):
    ohlc = get_ohlc_data(symbol, timeframe)

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=ohlc.index,
                open=ohlc['Open'],
                high=ohlc['High'],
                low=ohlc['Low'],
                close=ohlc['Close']
            )
        ])

    layout = go.Layout(
        paper_bgcolor='rgb(14, 17, 23)',
        plot_bgcolor='rgb(14, 17, 23)',
        font={'color': 'white'},
        hovermode='x'
    )
    
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=['sat', 'mon'])
        ]
    )

    fig.update_layout(layout)
    
    return fig.update_layout(xaxis_rangeslider_visible=False)


def display_pattern_recognition():
    # Pattern Recognition
    st.sidebar.header("Pattern Recognition")

    # st.sidebar.header("Ticker List")
    # symbol = st.sidebar.selectbox('Current Watchlist', watchlist)

    symbol = st.sidebar.text_input("Enter a symbol", 'AAPL')

    pattern_timeframe = st.sidebar.select_slider(
        'Select Pattern Recognition Timeframe',
        options=range(1, 366),
        value=30
    )
    
    st.sidebar.write(f"{symbol} Morning Star Candles")
    st.sidebar.dataframe(morning_star_candle(symbol, pattern_timeframe))

    st.sidebar.write(f"{symbol} Engulfing Candles")
    st.sidebar.dataframe(engulfing_candle(symbol, pattern_timeframe))

    # chart for sidebar stock
    with st.beta_expander(f'{symbol} Chart', True):
        st.plotly_chart(create_candle_chart(symbol, pattern_timeframe), use_container_width=True)
    
    with st.beta_expander('Candlestick Patterns', True):
        col1, col2 = st.beta_columns(2)
        
        col1.header('Morning Star Patterns')
        with col1:
            st.dataframe(morning_star_candle(symbol, pattern_timeframe))
        
        col2.header('Engulfing Patterns')
        with col2:
            st.dataframe(engulfing_candle(symbol, pattern_timeframe))