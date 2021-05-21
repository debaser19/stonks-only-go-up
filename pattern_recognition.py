import talib
import yfinance as yf
import datetime


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
