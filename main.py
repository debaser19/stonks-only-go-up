import streamlit as st
import plotly.graph_objects as go
import pattern_recognition
import positions
import pl_graph
import pattern_recognition
import ticker_news


def main():
    watchlist = ['DKNG', 'NET', 'TSLA', 'GM', 'ABNB', 'GNOG', 'SPY', 'RKT', 'NVDA', 'SQ', 'FMAC',
                 'IPOF', 'PLUG', 'AMD', 'AAPL', 'BB', 'TSM', 'WKHS', 'NIO', 'PLTR', 'GME', 'AMC',
                 'TLRY', 'SNAP', 'ALLY', 'MSFT', 'ATVI', 'PENN', 'INTC', 'AMZN', 'COST', 'ARKK',
                 'U', 'TWTR', 'ROKU', 'BAC', 'X', 'F']

    st.set_page_config(layout="wide") 
    # sidebar
    # dashboard selector
    dashboard_selection = st.sidebar.selectbox('Select Dashboard', options=[
        'P/L Graph',
        'Positions',
        'Pattern Recognition',
        'News'
    ])

    if dashboard_selection == 'P/L Graph':
        pl_graph.display_pl_graph()
    elif dashboard_selection == 'Positions':
        positions.display_positions()
    elif dashboard_selection == 'Pattern Recognition':
        pattern_recognition.display_pattern_recognition()
    elif dashboard_selection == 'News':
        ticker_news.display_news()
        

if __name__ == '__main__':
    main()
