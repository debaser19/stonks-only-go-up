import plotly          
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
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


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
current_balance = 0

# Layout Stuff
def createBalanceTable():
    return dash_table.DataTable(
        id = 'balance_table',
        columns = [
            {'name': 'Net Liquidity', 'id': 'net_liq'},
            {'name': 'Cash', 'id': 'cash'},
            {'name': 'Buying Power', 'id': 'buying_power'},
            {'name': 'Margin Balance', 'id': 'margin_balance'}
        ],
        style_header = {'background': '#333'},
        style_cell = {'background': '#444'}
    )


def createRadioButtons():
    return dcc.RadioItems(
        options = [
            {'label': '1D', 'value': '1d'},
            {'label': '7D', 'value': '7d'},
            {'label': '30D', 'value': '30d'},
            {'label': '3M', 'value': '90d'},
            {'label': '6M', 'value': '180d'},
            {'label': '1Y', 'value': '365d'}
        ],
        id = 'timeframe',
        value = '1d'
    )
    

def createTickerList():
    return html.Div([
        html.H3('Trading tickers')
    ])


def createGraph():
    return dcc.Graph(
        id='graph', 
        animate=False,
        figure = {
            'layout': go.Layout(
                paper_bgcolor = '#333',
                plot_bgcolor = '#333',
                font = {'color': 'white'}
            )
        }
    )


def createStonksTable():
    # TODO: Need to dymanically pull in headers for tables
    return dash_table.DataTable(
        id = 'stocks_table',
        columns = [
            {'name': 'Asset Type', 'id': 'asset_type'},
            {'name': 'Ticker', 'id': 'ticker'},
            {'name': 'Quantity', 'id': 'quantity'},
            {'name': 'Trade Price', 'id': 'trade_price'},
            {'name': 'Current Price', 'id': 'current_price'},
            {'name': 'Net Liquidity', 'id': 'pos_net_liq'},
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
                'color': 'royalblue'
            },
            {
                'if': { # negative p/l day
                    'filter_query': '{pl_day} < 0',
                    'column_id': ['pl_day', 'pl_day_percent']
                },
                'color': 'red'
            },
            {
                'if': { # positive p/l open
                    'filter_query': '{pl_open} > 0',
                    'column_id': ['pl_open']

                },
                'color': 'royalblue'
            },
            {
                'if': { # negative p/l open
                    'filter_query': '{pl_open} < 0',
                    'column_id': ['pl_open']
                },
                'color': 'red'
            }
        ],
        style_header = {'background': '#333'},
        style_cell = {'background': '#444'}
    )


def createOptionsTable():
    return dash_table.DataTable(
        id = 'options_table',
        columns = [
            {'name': 'Asset Type', 'id': 'asset_type'},
            {'name': 'Ticker', 'id': 'ticker'},
            {'name': 'Description', 'id': 'description'},
            {'name': 'Quantity', 'id': 'quantity'},
            {'name': 'Trade Price', 'id': 'trade_price'},
            {'name': 'Current Price', 'id': 'current_price'},
            {'name': 'Net Liquidity', 'id': 'pos_net_liq'},
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
                'color': 'royalblue'
            },
            {
                'if': { # negative p/l day
                    'filter_query': '{pl_day} < 0',
                    'column_id': ['pl_day', 'pl_day_percent']
                },
                'color': 'red'
            },
            {
                'if': { # positive p/l open
                    'filter_query': '{pl_open} > 0',
                    'column_id': ['pl_open']

                },
                'color': 'royalblue'
            },
            {
                'if': { # negative p/l open
                    'filter_query': '{pl_open} < 0',
                    'column_id': ['pl_open']
                },
                'color': 'red'
            }
        ],
        style_header = {'background': '#333'},
        style_cell = {'background': '#444'}
    )


app.layout = html.Div([
    dbc.Row(
        dbc.Col(html.Div(createBalanceTable()), width = {'size': 6, 'offset': 3})
    ),
    dbc.Row(
        dbc.Col(html.Div(createGraph()), width = {'size': 10, 'offset': 1})
    ),
    dbc.Row(
        dbc.Col(html.Div(createRadioButtons()), width = {'size': 3, 'offset': 5})
    ),
    html.H1('Positions'),
    html.H3('Stonks'),
    dbc.Row(
        dbc.Col(html.Div(createStonksTable()), width = {'size': 10, 'offset': 1})
    ),
    html.H3('Options'),
    dbc.Row(
        dbc.Col(html.Div(createOptionsTable()), width = {'size': 10, 'offset': 1})
    ),
    dcc.Interval(
        id = 'my-interval',
        interval = 10 * 1000,
        n_intervals = 0
    )
])


# CALLBACKS

# # Update balance on interval
# @app.callback(
#     Output('balance_table', 'data'),
#     [Input('my-interval', 'n_intervals')]
# )
# def updateBalance(num):
#     return [getBalances()]

# Update graph on interval
# TODO: Need to figure out how to preserve ui state on updates when user has panned or zoomed
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
        time_interval = '1h'
    elif timeframe == '90d':
        time_interval = '2h'
    elif timeframe == '180d':
        time_interval = '4h'
    elif timeframe == '365d':
        time_interval = '8h'
    else:
        time_interval = '168h'

    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, mean(value) as value from balance where time > now() - {timeframe} GROUP BY time({time_interval})'
    results = client.query(query)

    try:
        df = results['balance']
    except KeyError as e:
        print(f'KeyError: {e}')
        print(f'Unable to pull balance as no plot points in range, falling back to 7d')
        query = f'select time, mean(value) as value from balance where time > now() - 7d GROUP BY time(5m)'
        results = client.query(query)
        df = results['balance']
        
    df['timestamp'] = df.index

    data =[
        go.Scatter(
            y = df.value,
            x = df.timestamp.tz_convert('US/Eastern'),
            mode = 'lines',
            line = {'color': 'yellow'}
        )
    ]

    layout = go.Layout(
        title = emoji.emojize('This isn\'t where I parked my tendies --- HOTDOGS ---... :rocket::rocket::rocket:', use_aliases=True),
        uirevision = data,
        paper_bgcolor = '#333',
        plot_bgcolor = '#333',
        font = {'color': 'white'}
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
    Output('options_table', 'data'),
    Output('balance_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def updatePositions(num):
    all_positions = getPositions()
    stock_positions = all_positions[0]
    options_positions = all_positions[1]
    account_balance = all_positions[2]
    stonks_df = pd.DataFrame(stock_positions)
    options_df = pd.DataFrame(options_positions)
    print('Updating Stonks table...')
    print(stonks_df)
    print('Updating Options table...')
    print(options_df)

    return stonks_df.to_dict('records'), options_df.to_dict('records'), [account_balance]


# # Update option positions on interval
# @app.callback(
#     Output('options_table', 'data'),
#     [Input('my-interval', 'n_intervals')]
# )
# def updateOptionPositions(num):
#     options_positions = getPositions()[1]
#     df = pd.DataFrame(options_positions)
#     print('Updating Options table...')
#     print(df)

#     return df.to_dict('records')


# API Connection
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
    r = c.get_account(config.account_number, fields=c.Account.Fields.POSITIONS)
    account_info = r.json()
    print('Refreshing account info...')

    return account_info


def getPositions():
    account_info = getAccountInfo()
    stock_positions = []
    option_positions = []
    positions_list = account_info['securitiesAccount']['positions']
    
    for position in positions_list:

        long_quantity = position['longQuantity']
        short_quantity = position['shortQuantity']
        quantity = long_quantity - short_quantity
        trade_price = position['averagePrice']
        current_price = abs(position['marketValue']) / abs(long_quantity - short_quantity)
        pl_day = position['currentDayProfitLoss']
        pl_day_percent = position['currentDayProfitLossPercentage']
        ticker = position['instrument']['symbol']


        if quantity > 0:
            # long position
            pl_open = ((current_price - trade_price) * abs(quantity))
        else:
            # short position
            pl_open = ((trade_price - current_price) * abs(quantity))

        # check the asset type
        if position['instrument']['assetType'] == 'EQUITY': # asset type is shares

            stock_position_dict = {
                'asset_type': position['instrument']['assetType'],
                'ticker': ticker,
                'quantity': quantity,
                'trade_price': f'{trade_price:.2f}',
                'current_price': f'{current_price:.2f}',
                'pos_net_liq': f'{position["marketValue"]:.2f}',
                'pl_day': f'{pl_day:.2f}',
                'pl_day_percent': f'{pl_day_percent:.2f}',
                'pl_open': f'{pl_open:.2f}'
            }

            stock_positions.append(stock_position_dict)


        # asset type is an option, determine if call/put
        if position['instrument']['assetType'] == 'OPTION':
            if quantity > 0:
                # long position
                pl_open = (((current_price) / 100 - trade_price) * abs(quantity)) * 100
            else:
                # short position
                pl_open = ((trade_price - (current_price) / 100) * abs(quantity)) * 100

            option_position_dict = {
                'asset_type': position['instrument']['putCall'],
                'ticker': position['instrument']['symbol'],
                'description': position['instrument']['description'],
                'quantity': quantity,
                'trade_price': f'{trade_price:.2f}',
                'current_price': f'{current_price / 100:.2f}',
                'pos_net_liq': f'{position["marketValue"]:.2f}',
                'pl_day': f'{pl_day:.2f}',
                'pl_day_percent': f'{pl_day_percent:.2f}',
                'pl_open': f'{pl_open:.2f}'
            }

            option_positions.append(option_position_dict)

    list_of_tickers = []
    for stock_ticker in stock_positions:
        if stock_ticker['ticker'] not in list_of_tickers:
            list_of_tickers.append(stock_ticker['ticker'])
    
    for option_ticker in option_positions:
        t = option_ticker['ticker'].split('_')[0]
        if t not in list_of_tickers:
            list_of_tickers.append(t)

    
    print(f'List of tickers: {list_of_tickers}')

    balance_dict = {
        'net_liq': f"{account_info['securitiesAccount']['currentBalances']['liquidationValue']:,}",
        'cash': f"{account_info['securitiesAccount']['currentBalances']['availableFunds']:,}",
        'buying_power': f"{account_info['securitiesAccount']['currentBalances']['buyingPower']:,}",
        'margin_balance': f"{account_info['securitiesAccount']['currentBalances']['marginBalance']:,}"
    }
    
    return stock_positions, option_positions, balance_dict, list_of_tickers


# def getBalances():
#     account_info = getAccountInfo()
#     balance_dict = {
#         'net_liq': f"{account_info['securitiesAccount']['currentBalances']['liquidationValue']:,}",
#         'cash': f"{account_info['securitiesAccount']['currentBalances']['availableFunds']:,}",
#         'buying_power': f"{account_info['securitiesAccount']['currentBalances']['buyingPower']:,}",
#         'margin_balance': f"{account_info['securitiesAccount']['currentBalances']['marginBalance']:,}"
#     }

#     return balance_dict


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
