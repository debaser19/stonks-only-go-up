import ast
import plotly.graph_objects as go
from influxdb import DataFrameClient
import config


def get_current_positions(position):
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, {position} from balance group by * order by time desc limit 1'
    results = client.query(query)
    
    positions = results['balance'].iloc[0][position]

    # need to return the string representation of a list as a list
    return ast.literal_eval(positions)


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


def get_ticker_list():
    option_positions = get_current_positions('Options')
    option_tickers = [t['ticker'].split('_')[0] for t in option_positions]

    stock_positions = get_current_positions('Positions')
    stock_tickers = [t['ticker'] for t in stock_positions]

    return list(set(option_tickers) | set(stock_tickers))
