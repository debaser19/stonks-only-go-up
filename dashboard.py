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
    dash_table.DataTable(
        id = 'balance_table',
        columns = [
            {'name': 'Net Liquidity', 'id': 'net_liq'},
            {'name': 'Cash', 'id': 'cash'},
            {'name': 'Buying Power', 'id': 'buying_power'},
            {'name': 'Margin Balance', 'id': 'margin_balance'}
        ]
    ),
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
        ],
        style_data_conditional = [
            {
                'if': { # positive p/l day
                    'filter_query': '{pl_day} > 0',
                    'column_id': ['pl_day', 'pl_day_percent']

                },
                'backgroundColor': 'royalblue',
                'color': 'white'
            },
            {
                'if': { # negative p/l day
                    'filter_query': '{pl_day} < 0',
                    'column_id': ['pl_day', 'pl_day_percent']
                },
                'backgroundColor': 'red',
                'color': 'white'
            },
            {
                'if': { # positive p/l open
                    'filter_query': '{pl_open} > 0',
                    'column_id': ['pl_open']

                },
                'backgroundColor': 'royalblue',
                'color': 'white'
            },
            {
                'if': { # negative p/l open
                    'filter_query': '{pl_open} < 0',
                    'column_id': ['pl_open']
                },
                'backgroundColor': 'red',
                'color': 'white'
            }
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
        ],
        style_data_conditional = [
            {
                'if': { # positive p/l day
                    'filter_query': '{pl_day} > 0',
                    'column_id': ['pl_day', 'pl_day_percent']

                },
                'backgroundColor': 'royalblue',
                'color': 'white'
            },
            {
                'if': { # negative p/l day
                    'filter_query': '{pl_day} < 0',
                    'column_id': ['pl_day', 'pl_day_percent']
                },
                'backgroundColor': 'red',
                'color': 'white'
            },
            {
                'if': { # positive p/l open
                    'filter_query': '{pl_open} > 0',
                    'column_id': ['pl_open']

                },
                'backgroundColor': 'royalblue',
                'color': 'white'
            },
            {
                'if': { # negative p/l open
                    'filter_query': '{pl_open} < 0',
                    'column_id': ['pl_open']
                },
                'backgroundColor': 'red',
                'color': 'white'
            }
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
    Output('balance_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def updateBalance(num):
    return [getBalances()]

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
        title = emoji.emojize('AMC ded? :('),
        uirevision = data
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


# Update stock positions on interval
@app.callback(
    Output('stocks_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def updateStockPositions(num):
    stock_positions = getPositions()[0]
    df = pd.DataFrame(stock_positions)

    return df.to_dict('records')


# Update option positions on interval
@app.callback(
    Output('options_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def updateOptionPositionss(num):
    options_positions = getPositions()[1]
    df = pd.DataFrame(options_positions)

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
    
    for position in positions_list:
        quantity = position['longQuantity'] - position['shortQuantity']

        # TODO: Need to fix p/l calculations for options / short positions
        # Need to figure out formula for calculating the short positions correctly
        current_price = position['marketValue'] / abs(quantity)
        pl_open = position['marketValue'] - position['averagePrice'] * abs(quantity)

        # check the asset type
        if position['instrument']['assetType'] == 'EQUITY': # asset type is shares

            stock_position_dict = {
                'asset_type': position['instrument']['assetType'],
                'ticker': position['instrument']['symbol'],
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'trade_price': f"{position['averagePrice']:.2f}",
                'current_price': f'{current_price:.2f}',
                'pl_day': position['currentDayProfitLoss'],
                'pl_day_percent': position['currentDayProfitLossPercentage'],
                'pl_open': f'{pl_open:.2f}'
            }

            stock_positions.append(stock_position_dict)

        # asset type is an option, determine if cal/put
        else:

            option_position_dict = {
                'asset_type': position['instrument']['putCall'],
                'ticker': position['instrument']['underlyingSymbol'],
                'description': position['instrument']['description'],
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'trade_price': f"{position['averagePrice']:.2f}",
                'current_price': f"{abs(current_price) / 100:.2f}",
                'pl_day': position['currentDayProfitLoss'],
                'pl_day_percent': position['currentDayProfitLossPercentage'],
                'pl_open': 'fixme'
            }

            option_positions.append(option_position_dict)
    
    return stock_positions, option_positions


def getBalances():
    account_info = getAccountInfo()
    balance_dict = {
        'net_liq': f"{account_info['securitiesAccount']['currentBalances']['liquidationValue']:,}",
        'cash': f"{account_info['securitiesAccount']['currentBalances']['availableFunds']:,}",
        'buying_power': f"{account_info['securitiesAccount']['currentBalances']['buyingPower']:,}",
        'margin_balance': f"{account_info['securitiesAccount']['currentBalances']['marginBalance']:,}"
    }

    return balance_dict


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
