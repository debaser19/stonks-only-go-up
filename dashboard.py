import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from influxdb import InfluxDBClient, DataFrameClient
import config
import time


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


client = DataFrameClient('localhost', 8086, config.influxdb_user, config.influxdb_pass, 'balance_history')
query = 'select * from balance'
results = client.query(query)
df = results['balance']
df['timestamp'] = df.index
print(df)

fig = px.line(df, x="timestamp", y="value", title='Sweet Tendies')

app.layout = html.Div([
    dcc.Graph(figure=fig)
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
