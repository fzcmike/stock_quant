"""
RSI策略 - 相对强弱指数
RSI<30超卖买入，RSI>70超买卖出
"""
import pandas as pd
import numpy as np

class RSIStrategy:
    name = "RSI策略"

    def __init__(self, period=14, oversold=30, overbought=70, **kwargs):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss.replace(0, np.inf)
        df['rsi'] = 100 - (100 / (1 + rs))

        df['signal'] = 0
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1   # 买入
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1  # 卖出
        # 只在信号变化时产生交易信号（signal_change用于检测交叉点）
        df['signal_change'] = df['signal'].diff()

        return df[['date', 'close', 'rsi', 'signal', 'signal_change']].dropna()

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        signals = self.generate_signals(data)
        if signals.empty:
            return {'action': 'hold', 'price': None}
        last = signals.iloc[-1]
        if last['signal_change'] > 0:
            return {'action': 'buy', 'price': last['close'], 'rsi': round(last['rsi'], 2)}
        elif last['signal_change'] < 0:
            return {'action': 'sell', 'price': last['close'], 'rsi': round(last['rsi'], 2)}
        return {'action': 'hold', 'price': last['close'], 'rsi': round(last['rsi'], 2)}
