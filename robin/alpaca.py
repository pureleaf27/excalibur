import requests
import json
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from secret import API_KEY, API_SECRET
from textblob import TextBlob
# endpoint = "https://paper-api.alpaca.markets/"

API_BASE_URL = "https://api.polygon.io/"

stock_ticker_data = "v2/aggs/ticker/"
stock_news = "v1/meta/symbols/{}/news/"
# https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2019-01-01/2019-02-01?apiKey=PKJXKK531LV55MJUPP1N

def _get(url, query_param=None):
    if query_param is not None:
        query_param = "?apiKey={}".format(API_KEY) + "&{}".format(query_param)
    else:
        query_param = "?apiKey={}".format(API_KEY)
    url = url + query_param
    print("GET: {}".format(url))
    response = requests.get(url)
    return response

def get_sentiment(text):
    opinion = TextBlob(text)
    return opinion.sentiment.polarity

def get_stock_sentiment(ticker, timeframes):
    url = API_BASE_URL + stock_news.format(ticker)
    resp = _get(url)
    resp_json = resp.json()
    positives = 0
    negatives = 0

    for item in resp_json:
        date_ = datetime.datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").date()
        if date_ not in timeframes:
            continue
        print(date_)
        summary = item.get("summary")
        sentiment = get_sentiment(summary)
        if sentiment > 0:
            positives += 1
        elif sentiment < 0:
            negatives += 1
    ret = 0
    if positives > negatives:
        ret = 1
    elif negatives > positives:
        ret = -1
    return ret

def get_stock_data(ticker, range_info=None):
    url = API_BASE_URL + stock_ticker_data + ticker
    now_ = datetime.datetime.now()
    date_ = datetime.datetime.strftime(now_, "%Y-%m-%d")

    assert set(list(["period", "type", "start", "end"])) == set(range_info.keys())
    if range_info is not None:
        sub_url = "/range/" + "{}".format(range_info["period"]) + "/" + range_info["type"]
        if range_info.get("start") is None and range_info.get("end") is None:
            range_info["start"] = date_
            range_info["end"] = date_
        sub_url += "/{}/{}".format(range_info.get("start"), range_info.get("end"))
        url += sub_url
    # print(url)

    resp = _get(url, query_param="unadjusted=false")
    return resp.json()


def set_range_info(period, type, start=None, end=None):
    range_info = {
        "period": period,
        "type": type,
        "start": start,
        "end": end
    }
    now_ = datetime.datetime.now()
    date_ = datetime.datetime.strftime(now_, "%Y-%m-%d")

    if start is None:
        range_info["start"] = date_
    if end is None:
        range_info["end"] = date_
    return range_info


def get_df(resp):
    df = None
    if resp.get("resultsCount") > 0:
        df = pd.DataFrame(resp.get("results"))
        df.t = pd.to_datetime(df["t"], unit='ms')
        df.set_index('t', inplace=True)

        for col in df.columns:
            if df[col].dtype == np.object:
                try:
                    df[col] = df[col].astype(np.float64)
                except Exception:
                    pass
    return df


def plot_candles(df, ticker, range_info):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['o'], high=df['h'],
                                         low=df['l'], close=df['c'])
                          ])
    fig.update_layout(xaxis_rangeslider_visible=True,
                      title='{} Candlesticks ({} {})'.format(ticker,
                                                             range_info["period"],
                                                             range_info["type"]))
    fig.layout.xaxis.type = "category"
    return fig


def pvi_index(df): #Index(['v', 'o', 'c', 'h', 'l', 'n'], dtype='object')
    df['pvi'] = 1000
    df['pvi'].iloc[0] = 1000
    price_rate = ((df['c'] - df['c'].shift(1))/df['c'])

    pvi = df['pvi']
    for i, index in enumerate(df['pvi'].index):
        if i == 0:
            continue
        prev_pvi = pvi.iloc[i-1]

        if df['v'].iloc[i] <= df['v'].iloc[i-1]:
            pvi[index] = pvi.iloc[i-1]
        else:
            pvi[index] = prev_pvi + (price_rate.iloc[i] * prev_pvi)
    return pvi


def pvi_beeps(pvi_series, tick_count=1):
    count = len(pvi_series.index)
    if tick_count > count:
        return None
    a = pvi_series.iloc[count-tick_count-1]
    b = pvi_series.iloc[count-1]
    if b/a > 1.5:
        return True
    return False

def find_all_pvi_beepers():
    with open('all_ticker.csv', 'r') as f:
        content = f.read()
    tickers = content.split(",")
    for i, ticker in enumerate(tickers):
        print(i, ticker)
        range_info = set_range_info(1, "day", "2020-01-01", "2020-04-15")
        resp = get_stock_data(ticker, range_info)
        df = get_df(resp)  # Index(['v', 'o', 'c', 'h', 'l', 'n'], dtype='object')
        try:
            pvi = pvi_index(df)
            if pvi_beeps(pvi, tick_count=3):
                print("{} beeped".format(ticker))
                beeped.append(ticker)
        except Exception:
            pass
    return beeped

def plot_series(series_, ticker, range_info, desc=None):
    fig = go.Figure(data=[go.Bar(x=series_.index, y=series_)
                          ])
    fig.update_layout(xaxis_rangeslider_visible=True,
                      title='{} {} ({} {})'.format(ticker,
                                                   desc,
                                                   range_info["period"],
                                                   range_info["type"]))
    fig.layout.xaxis.type = "category"
    return fig

def get_all_tickers():
    resp = _get("https://api.polygon.io/v2/aggs/grouped/locale/US/market/STOCKS/2020-04-15", "unadjusted=false")
    j = resp.json()
    ddf = pd.DataFrame(j['results'])
    ddf.T.to_csv('all_ticker.csv', index=False)  ##needs fix

if __name__ == '__main__':
    beeped = list()
    beeping_ticks = find_all_pvi_beepers()
    print(beeping_ticks)
    # range_info = set_range_info(1, "day", "2019-04-01", "2020-04-15")
    # ticker = "WORX"
    # resp = get_stock_data(ticker, range_info)
    # df = get_df(resp)  #Index(['v', 'o', 'c', 'h', 'l', 'n'], dtype='object')

    # pvi = pvi_index(df)
    # pvi_beeps(pvi, tick_count=3)
    # fig = plot_series(pvi, ticker, range_info, desc="PVI")

    # fig = plot_series(df['v'], ticker, range_info)
    # fig.show()

    # fig = plot_series(df['v'], ticker, range_info, desc="Volume")
    # fig = plot_series(df['v'], ticker, range_info)
    # fig.show()
    # fig = plot_candles(df, ticker, range_info)
    # fig.show()
    # print(df)

    # timeframes = [datetime.datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S").date() for x in df.index]
    # resp = get_stock_sentiment(ticker, timeframes)
    1==1





