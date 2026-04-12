"""
布林带策略
价格触及下轨买入，价格触及上轨卖出
"""
import pandas as pd
import numpy as np

class BollingerStrategy:
    name = "布林带策略"

    def __init__(self, period=20, std_dev=2, **kwargs):
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['mid'] = df['close'].rolling(window=self.period).mean()
        std = df['close'].rolling(window=self.period).std()
        df['upper'] = df['mid'] + std * self.std_dev
        df['lower'] = df['mid'] - std * self.std_dev

        # 信号：价格突破布林带
        df['signal'] = 0
        df.loc[df['close'] < df['lower'], 'signal'] = 1   # 买入（超卖）
        df.loc[df['close'] > df['upper'], 'signal'] = -1  # 卖出（超买）
        df['signal_change'] = df['signal'].diff()
        return df[['date', 'close', 'mid', 'upper', 'lower', 'signal', 'signal_change']].dropna()

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        signals = self.generate_signals(data)
        if signals.empty:
            return {'action': 'hold', 'price': None}
        last = signals.iloc[-1]
        if last['signal_change'] > 0:
            return {'action': 'buy', 'price': last['close'],
                    '布林下轨': round(last['lower'], 2), '当前价': round(last['close'], 2)}
        elif last['signal_change'] < 0:
            return {'action': 'sell', 'price': last['close'],
                    '布林上轨': round(last['upper'], 2), '当前价': round(last['close'], 2)}
        return {'action': 'hold', 'price': last['close'],
                '布林中轨': round(last['mid'], 2), '布林上轨': round(last['upper'], 2), '布林下轨': round(last['lower'], 2)}
