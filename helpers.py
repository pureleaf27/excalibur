import pandas as pd
import numpy as np
import os

class Stock:
    def __init__(self, r):
        self.r = r
    
    def get_df(self, symbol, span="day"):
        dat = self.r.get_historicals(symbol, span=span)
        df = pd.DataFrame(dat)
        df.begins_at = pd.to_datetime(df['begins_at'], format='%Y-%m-%dT%H:%M:%SZ')
        df.set_index('begins_at', inplace=True)

        for col in df.columns:
            if df[col].dtype == np.object:
                try:
                    df[col] = df[col].astype(np.float64)
                except Exception:
                    pass
        return df
    
    def get_diff_df(self, df, columns=["close_diff", "open_diff", "high_diff", "low_diff"]):
        close_diff = df.close_price.shift(1) - df.close_price
        open_diff = df.open_price.shift(1) - df.open_price
        high_diff = df.high_price.shift(1) - df.high_price
        low_diff = df.low_price.shift(1) - df.low_price

        diff_df = pd.DataFrame(list(zip(close_diff, open_diff, high_diff, low_diff)), 
             columns=columns)
        diff_df.index = df.index
        return diff_df
    
    def _roc(self, curr, prev):
        return ((curr-prev)/prev)*100
    
    def get_roc_df(self, df, columns=["close_roc", "open_roc", "high_roc", "low_roc"]):
        close_roc = self._roc(df.close_price.shift(1), df.close_price)
        open_roc = self._roc(df.open_price.shift(1), df.open_price)
        high_roc = self._roc(df.high_price.shift(1), df.high_price)
        low_roc = self._roc(df.low_price.shift(1), df.low_price)

        diff_df = pd.DataFrame(list(zip(close_roc, open_roc, high_roc, low_roc)), 
             columns=columns)
        diff_df.index = df.index
        return diff_df
    
    def get_acc_roc_df(self, df, columns=["close_roc", "open_roc", "high_roc", "low_roc"]):
        close_roc = self._roc(df.close_roc.shift(1), df.close_roc)
        open_roc = self._roc(df.open_roc.shift(1), df.open_roc)
        high_roc = self._roc(df.high_roc.shift(1), df.high_roc)
        low_roc = self._roc(df.low_roc.shift(1), df.low_roc)

        diff_df = pd.DataFrame(list(zip(close_roc, open_roc, high_roc, low_roc)), 
             columns=columns)
        diff_df.index = df.index
        return diff_df
    
    def get_volume_roc_df(self, df, columns=["volume"]):
        volume_roc = self._roc(df.volume.shift(1), df.volume)

        diff_df = pd.DataFrame(volume_roc, columns=columns)
        diff_df.index = df.index
        return diff_df
    