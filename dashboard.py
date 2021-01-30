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


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Graph(id='graph', animate=True),
    dcc.Interval(
        id = 'my-interval',
        interval = 5 * 1000,
        n_intervals = 0
    )
])

# callback for updating on interval
@app.callback(
    Output('graph', 'figure'),
    [Input('my-interval', 'n_intervals')]
)
def updateGraph(num):
    # connect to influx and import to df
    client = DataFrameClient('localhost', 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
    query = 'select * from balance where time > now() - 24h'
    results = client.query(query)
    df = results['balance']
    df['timestamp'] = df.index
    df['timestamp'] = df['timestamp'].tz_convert('US/Eastern')

    # TODO: Need to fix the auto updating. It seems to updat ethe line data, but not the axis data

    data =[
        go.Scatter(
            y = df.value,
            x = df.timestamp,
            mode = 'lines'
        )
    ]

    layout = go.Layout(
        title = 'Sweet Tendies'
    )
    fig = go.Figure(data=data, layout=layout)

    # print(client.query('select last("value") as value from balance'))

    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
