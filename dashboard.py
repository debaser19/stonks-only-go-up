import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
from influxdb import DataFrameClient
import config
import emoji
import yfinance
import ast
import config
import positions


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def create_balance_table():
    return dash_table.DataTable(
        id = 'balance_table',
        columns = [
            {'name': 'NetLiquidity', 'id': 'NetLiq'},
            {'name': 'Cash', 'id': 'Cash'},
            {'name': 'Buying Power', 'id': 'BuyingPower'},
            {'name': 'Margin Balance', 'id': 'MarginBalance'}
        ],
        style_header = {'background': 'rgb(14, 17, 23)'},
        style_cell = {'background': 'rgb(30, 33, 39)'}
    )


def create_pl_graph():
    return dcc.Graph(
        id='graph', 
        animate=False,
        figure = {
            'layout': go.Layout(
                paper_bgcolor = 'rgb(14, 17, 23)',
                plot_bgcolor = 'rgb(14, 17, 23)',
                font = {'color': 'white'}
            )
        }
    )


def create_stonks_table():
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
                'color': 'lightgreen '
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
                'color': 'lightgreen '
            },
            {
                'if': { # negative p/l open
                    'filter_query': '{pl_open} < 0',
                    'column_id': ['pl_open']
                },
                'color': 'red'
            }
        ],
        style_header = {'background': 'rgb(14, 17, 23)'},
        style_cell = {'background': 'rgb(30, 33, 39)'}
    )


def create_options_table():
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
                'color': 'lightgreen '
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
                'color': 'lightgreen '
            },
            {
                'if': { # negative p/l open
                    'filter_query': '{pl_open} < 0',
                    'column_id': ['pl_open']
                },
                'color': 'red'
            }
        ],
        style_header = {'background': 'rgb(14, 17, 23)'},
        style_cell = {'background': 'rgb(30, 33, 39)'}
    )


# Callbacks
# Update graph on interval
# TODO: Need to figure out how to preserve ui state on updates when user has panned or zoomed
@app.callback(
    Output('graph', 'figure'),
    [Input('my-interval', 'n_intervals'),
    Input('timeframe', 'value')]
)
def update_graph(num, timeframe):
    # connect to influx and import to df
    tz_offset = 4

    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = f'select time, NetLiq from balance where time > now() - {tz_offset}h - {timeframe}h'
    results = client.query(query)
    df = pd.DataFrame(results['balance'])
    df['NetLiq'] = pd.to_numeric(df['NetLiq'], downcast='float')
    df['Date'] = df.index

    # check if red or green
    if df.NetLiq.iloc[0] < df.NetLiq.iloc[-1]:
        line_color = 'lightgreen'
    elif df.NetLiq.iloc[0] > df.NetLiq.iloc[-1]:
        line_color = 'red'
    else:
        line_color = 'yellow'

    data =[
        go.Scatter(
            y = df.NetLiq,
            x = df.Date,
            mode = 'lines',
            line = {'color': line_color}
        )
    ]
    if timeframe <= 24:
        title_time = f'{int(timeframe)} hour(s)'
    elif timeframe >= 24 and timeframe < 720:
        title_time = f'{int(timeframe / 24)} day(s)'
    elif timeframe >= 720 and timeframe < 8760:
        title_time = f'{int(timeframe / (24 * 30))} month(s)'
    else:
        title_time = f'{(int(timeframe / (24 * 365)))} year(s)'
    layout = go.Layout(
        title = emoji.emojize(f'Portfolio performance over the past {title_time}', use_aliases=True),
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

# Update stock positions on interval
@app.callback(
    Output('balance_table', 'data'),
    Output('stocks_table', 'data'),
    Output('options_table', 'data'),
    [Input('my-interval', 'n_intervals')]
)
def update_positions(num):
    # get balances
    client = DataFrameClient(config.influx_host, 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    balance_query = 'select time, BuyingPower, Cash, MarginBalance, NetLiq from balance group by * order by time desc limit 1'
    balance_results = client.query(balance_query)
    account_balance = balance_results['balance']
    account_balance = pd.DataFrame(account_balance).to_dict('records')

    # get positions
    positions_query = f'select time, Positions from balance group by * order by time desc limit 1'
    position_results = client.query(positions_query)
    
    positions = position_results['balance'].iloc[0]['Positions']

    # get options
    options_query = f'select time, Options from balance group by * order by time desc limit 1'
    option_results = client.query(options_query)
    
    options = option_results['balance'].iloc[0]['Options']

    return account_balance, ast.literal_eval(positions), ast.literal_eval(options)


# Layout
app.layout = html.Div([
    dbc.Row(
        dbc.Col(html.Div(create_balance_table()), width = {'size': 6, 'offset': 3})
    ),
    dcc.Tabs(
        id="dash-tabs",
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
        dcc.Tab(
            label='P/L Graph',
            className='pl-graph-tab dash-tab',
            selected_className='pl-graph-tab--selected dash-tab--selected',
            children=[
            dbc.Row(
                dbc.Col(html.Div(create_pl_graph()), width = {'size': 10, 'offset': 1})
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Slider(
                        min=1,
                        max=8760,
                        step=None,
                        marks={
                            1: '1H',
                            2: '2H',
                            3: '3H',
                            6: '6H',
                            12: '12H',
                            24: '1D',
                            168: '1W',
                            720: '1M',
                            1440: '2M',
                            2160: '3M',
                            4320: '6M',
                            8760: '1Y'
                        },
                        value=24,
                        id='timeframe'
                    )
                )
            )
        ]),
        dcc.Tab(
            label='Positions',
            className='positions-tab dash-tab',
            selected_className='positions-tab--selected dash-tab--selected',
            children=[
            dbc.Row(
                dbc.Col(html.Div([
                    html.H1('Positions'),
                    html.H3('Stocks'),
                    create_stonks_table()
                ]), width = {'size': 10, 'offset': 1})
            ),
            dbc.Row(
                dbc.Col(html.Div([
                    html.H3('Options'),
                    create_options_table()
                ]), width = {'size': 10, 'offset': 1})
            )
        ]),
        dcc.Tab(
            label='Pie Charts',
            className='pie-charts-tab dash-tab',
            selected_className='pie-charts-tab--selected dash-tab--selected',
            children=[
                dbc.Row(
                    dbc.Col(html.Div(
                        positions.get_portfolio_percentages()[1]
                        ), width={'size': 10, 'offset': 1}
                    )
                )
            ]
        ),
        dcc.Tab(
            label='Pattern Recognition',
            className='pattern-recognition-tab dash-tab',
            selected_className='pattern-recognition-tab--selected dash-tab--selected',
            children=[
                dbc.Row(
                    dbc.Col(html.Div([
                        html.H1('CANDLES!!')
                        ]), width={'size': 10, 'offset': 1}
                    )
                )
            ]
        )
    ]),
    dcc.Interval(
        id = 'my-interval',
        interval = 10 * 1000,
        n_intervals = 0
    )
])


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)