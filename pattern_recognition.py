import talib
import yfinance as yf
import datetime


def morning_star(symbol, timeframe):
    today = datetime.datetime.today()
    days = datetime.timedelta(timeframe)

    start_date = (today - days).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    data = yf.download(symbol, start=start_date, end=end_date)

    morningstar = talib.CDLMORNINGSTAR(data['Open'], data['High'], data['Low'], data['Close'])

    # TODO: Broken, need to fix
    if not morningstar[morningstar != 0].empty():
        return morningstar[morningstar != 0]
    else:
        return f'No morning star pattern in {timeframe}'


def engulfing(symbol, timeframe):
    today = datetime.datetime.today()
    days = datetime.timedelta(timeframe)

    start_date = (today - days).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    data = yf.download(symbol, start=start_date, end=end_date)

    engulfing = talib.CDLENGULFING(data['Open'], data['High'], data['Low'], data['Close'])

    # TODO: Broken, need to fix
    if not engulfing[engulfing != 0].empty():
        return engulfing[engulfing != 0]
    else:
        return f'No engulfing pattern in {timeframe}'


def main():
    symbol = 'DKNG'
    morning_star(symbol, 60)
    engulfing(symbol, 60)


if __name__ == '__main__':
    main()
