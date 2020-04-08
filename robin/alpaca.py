import requests
import json
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# endpoint = "https://paper-api.alpaca.markets/"

API_KEY = "PKJXKK531LV55MJUPP1N"
API_SECRET = "Tp/NtBacOF1POOX/PIF/gQfuqDMIfyHDZawjeA5B"
API_BASE_URL = "https://api.polygon.io/v2/"

stock_ticker_data = "aggs/ticker/"
# https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2019-01-01/2019-02-01?apiKey=PKJXKK531LV55MJUPP1N

def _get(url):
    print("GET: {}".format(url))
    response = requests.get(url)
    return response


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
        url += sub_url + "?apiKey={}".format(API_KEY)
    print(url)

    resp = _get(url)
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


def plot(df, ticker, range_info):
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

if __name__ == '__main__':
    range_info = set_range_info(1, "minute", "2020-04-01", "2020-04-06")

    ticker = "AVXL"
    resp = get_stock_data(ticker, range_info)
    df = get_df(resp)
    fig = plot(df, ticker, range_info)

    fig.show()
    print(df)



