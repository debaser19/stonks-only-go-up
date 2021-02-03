import plotly          
import plotly.graph_objects as go

import dash             
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output
# import plotly.express as px
import pandas as pd
from influxdb import InfluxDBClient, DataFrameClient
import config
import time
import pytz
import emoji
from tda import auth, client
import config


api_key = config.api_key
token_path = config.token_path
redirect_uri = config.redirect_uri


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
current_balance = 0

app.layout = html.Div([
    html.H1(
        id = 'balance-h1',
        # TODO: Need to pull in other balance info such as margin and cash values
        children = f'Current Balance: {current_balance}'),
    dcc.RadioItems(
        options = [
            {'label': '1D', 'value': '1d'},
            {'label': '7D', 'value': '7d'},
            {'label': '30D', 'value': '30d'},
            {'label': '3M', 'value': '90d'},
            {'label': '6M', 'value': '180d'},
            {'label': '1Y', 'value': '365d'}
        ],
        id = 'timeframe',
        value = '1d',
        labelStyle = {'display': 'inline-block'}
    ),
    dcc.Graph(id='graph', animate=False),
    html.H1('Positions'),
    html.H3('Stonks'),
    # TODO: Need to dymanically pull in headers for tables
    dash_table.DataTable(
        id = 'stocks_table',
        columns = [
            {'name': 'Asset Type', 'id': 'asset_type'},
            {'name': 'Ticker', 'id': 'ticker'},
            {'name': 'Quantity', 'id': 'quantity'},
            {'name': 'Trade Price', 'id': 'trade_price'},
            {'name': 'Current Price', 'id': 'current_price'},
            {'name': 'P/L Day', 'id': 'pl_day'},
            {'name': 'P/L Day %', 'id': 'pl_day_percent'},
            {'name': 'P/L Open', 'id': 'pl_open'}
        ]
    ),
    html.H3('Options'),
    dash_table.DataTable(
        id = 'options_table',
        columns = [
            {'name': 'Asset Type', 'id': 'asset_type'},
            {'name': 'Ticker', 'id': 'ticker'},
            {'name': 'Description', 'id': 'description'},
            {'name': 'Quantity', 'id': 'quantity'},
            {'name': 'Trade Price', 'id': 'trade_price'},
            {'name': 'Current Price', 'id': 'current_price'},
            {'name': 'P/L Day', 'id': 'pl_day'},
            {'name': 'P/L Day %', 'id': 'pl_day_percent'},
            {'name': 'P/L Open', 'id': 'pl_open'}
        ]
    ),
    dcc.Interval(
        id = 'my-interval',
        interval = 5 * 1000,
        n_intervals = 0
    )
])


# Update balance on interval
@app.callback(
    Output('balance-h1', 'children'),
    [Input('my-interval', 'n_intervals')]
)
def updateBalance(num):
    client = DataFrameClient('localhost', 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select last(value) as value from balance'
    results = client.query(query)
    df = results['balance']
    current_balance = df['value'].iloc[-1]

    return html.H1(id = 'balance-h1', children = f'Current balance: {current_balance}')


# Update graph on interval
@app.callback(
    Output('graph', 'figure'),
    [Input('my-interval', 'n_intervals'),
    Input('timeframe', 'value')]
)
def updateGraph(num, timeframe):
    # connect to influx and import to df
    if timeframe == '1d':
        time_interval = '30s'
    elif timeframe == '7d':
        time_interval = '5m'
    elif timeframe == '30d':
        time_interval = '2h'
    elif timeframe == '90d':
        time_interval = '1d'
    elif timeframe == '180d':
        time_interval = '3d'
    elif timeframe == '365d':
        time_interval = '7d'
    else:
        time_interval = '7d'

    client = DataFrameClient('localhost', 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, mean(value) as value from balance where time > now() - {timeframe} GROUP BY time({time_interval})'
    results = client.query(query)
    df = results['balance']
    df['timestamp'] = df.index

    data =[
        go.Scatter(
            y = df.value,
            x = df.timestamp.tz_convert('US/Eastern'),
            mode = 'lines'
        )
    ]

    layout = go.Layout(
        title = emoji.emojize('AMC ded? :(')
    )
    fig = go.Figure(data=data, layout=layout)

    fig.update_xaxes(tickformat = '%I:%M %p\n%x')

    return fig


# Update stock positions on interval
@app.callback(
    Output('stocks_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def updateStockPositions(num):
    stock_positions = getPositions()[0]
    df = pd.DataFrame(stock_positions)
    print(df.to_dict('data'))

    return df.to_dict('records')


# Update option positions on interval
@app.callback(
    Output('options_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def updateOptionPositionss(num):
    options_positions = getPositions()[1]
    df = pd.DataFrame(options_positions)
    print(df.to_dict('data'))

    return df.to_dict('records')


def connectToApi():
    # generate token
    try:
        c = auth.client_from_token_file(token_path, api_key)
        return c
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(
                driver, api_key, redirect_uri, token_path)


def getAccountInfo():
    c = connectToApi()
    r = c.get_account('455720137', fields=c.Account.Fields.POSITIONS)
    account_info = r.json()

    return account_info


def getPositions():
    account_info = getAccountInfo()
    stock_positions = []
    option_positions = []
    positions_list = account_info['securitiesAccount']['positions']

    # TODO: Need to add in current price and p/l open values
    
    for position in positions_list:

        # check the asset type
        if position['instrument']['assetType'] == 'EQUITY': # asset type is shares

            stock_position_dict = {
                'asset_type': position['instrument']['assetType'],
                'ticker': position['instrument']['symbol'],
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'trade_price': position['averagePrice'],
                'current_price': 'fixme',
                'pl_day': position['currentDayProfitLoss'],
                'pl_day_percent': position['currentDayProfitLossPercentage'],
                'pl_open': 'fixme'
            }

            stock_positions.append(stock_position_dict)

        # asset type is an option, determine if cal/put
        else:

            option_position_dict = {
                'asset_type': position['instrument']['putCall'],
                'ticker': position['instrument']['underlyingSymbol'],
                'description': position['instrument']['description'],
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'trade_price': position['averagePrice'],
                'current_price': 'fixme',
                'pl_day': position['currentDayProfitLoss'],
                'pl_day_percent': position['currentDayProfitLossPercentage'],
                'pl_open': 'fixme'
            }

            option_positions.append(option_position_dict)
    
    return stock_positions, option_positions


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
