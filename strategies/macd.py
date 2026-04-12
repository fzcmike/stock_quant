"""
MACD策略
MACD金叉买入，死叉卖出
"""
import pandas as pd
import numpy as np

class MACDStrategy:
    name = "MACD策略"

    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def calculate_ema(self, series, span):
        return series.ewm(span=span, adjust=False).mean()

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        ema_fast = self.calculate_ema(df['close'], self.fast)
        ema_slow = self.calculate_ema(df['close'], self.slow)
        df['macd'] = ema_fast - ema_slow
        df['signal_line'] = self.calculate_ema(df['macd'], self.signal)
        df['histogram'] = df['macd'] - df['signal_line']

        # 金叉/死叉
        df['signal'] = 0
        df.loc[df['histogram'] > 0, 'signal'] = 1
        df.loc[df['histogram'] <= 0, 'signal'] = -1

        df['signal_change'] = df['signal'].diff()

        return df[['date', 'close', 'macd', 'signal_line', 'histogram', 'signal', 'signal_change']].dropna()

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        signals = self.generate_signals(data)
        if signals.empty:
            return {'action': 'hold', 'price': None}

        last = signals.iloc[-1]

        if last['signal_change'] > 0:
            return {'action': 'buy', 'price': last['close'], 'date': str(last['date']),
                    'macd': round(last['macd'], 4), 'signal_line': round(last['signal_line'], 4)}
        elif last['signal_change'] < 0:
            return {'action': 'sell', 'price': last['close'], 'date': str(last['date']),
                    'macd': round(last['macd'], 4), 'signal_line': round(last['signal_line'], 4)}
        else:
            return {'action': 'hold', 'price': last['close'], 'date': str(last['date']),
                    'macd': round(last['macd'], 4), 'signal_line': round(last['signal_line'], 4)}
