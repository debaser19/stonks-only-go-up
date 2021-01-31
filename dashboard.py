import plotly          
import plotly.graph_objects as go

import dash             
import dash_core_components as dcc
import dash_html_components as html
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


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.RadioItems(
        options = [
            {'label': '1D', 'value': '1d'},
            {'label': '7D', 'value': '7d'},
            {'label': '30D', 'value': '30d'},
            {'label': '3M', 'value': '90d'},
            {'label': '6M', 'value': '180d'},
            {'label': '1Y', 'value': '365d'},
            {'label': 'ALL', 'value': 'all'}
        ],
        id = 'timeframe',
        value = '1d',
        labelStyle = {'display': 'inline-block'}
    ),
    dcc.Graph(id='graph', animate=False),
    dcc.Interval(
        id = 'my-interval',
        interval = 5 * 1000,
        n_intervals = 0
    )
])


# callback for updating on interval
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
    eastern = pytz.timezone('US/Eastern')
    df['timestamp'] = df['timestamp'].tz_convert(eastern)

    # TODO: Need to fix the auto updating. It seems to updat ethe line data, but not the axis data

    data =[
        go.Scatter(
            y = df.value,
            x = df.timestamp.tz_convert(eastern),
            mode = 'lines'
        )
    ]

    layout = go.Layout(
        title = emoji.emojize('AMC MOON :rocket: :rocket: :rocket: :rocket: :full_moon: :full_moon: :full_moon:')
    )
    fig = go.Figure(data=data, layout=layout)

    # print(client.query('select last("value") as value from balance'))
    # print(df)

    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
