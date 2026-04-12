"""
KDJ策略 - 随机指标
K从下穿越D买入，K从上穿越D卖出
"""
import pandas as pd
import numpy as np

class KDJStrategy:
    name = "KDJ策略"

    def __init__(self, n=9, m1=3, m2=3, **kwargs):
        self.n = n  # RSV周期
        self.m1 = m1  # K周期
        self.m2 = m2  # D周期

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        low_n = df['low'].rolling(window=self.n).min()
        high_n = df['high'].rolling(window=self.n).max()
        # 防止除零：当价格横盘时（high_n==low_n），RSV=50（中性值）
        price_range = high_n - low_n
        price_range = price_range.replace(0, np.nan)
        rsv = (df['close'] - low_n) / price_range * 100
        rsv = rsv.fillna(50)

        df['K'] = rsv.ewm(alpha=1/self.m1, adjust=False).mean()
        df['D'] = df['K'].ewm(alpha=1/self.m2, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']

        df['signal'] = 0
        # K上穿D（金叉）且J<50买入，K下穿D（死叉）且J>50卖出
        df.loc[(df['K'] > df['D']) & (df['J'] < 50), 'signal'] = 1
        df.loc[(df['K'] < df['D']) & (df['J'] > 50), 'signal'] = -1
        df['signal_change'] = df['signal'].diff()
        return df[['date', 'close', 'K', 'D', 'J', 'signal', 'signal_change']].dropna()

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        signals = self.generate_signals(data)
        if signals.empty:
            return {'action': 'hold', 'price': None}
        last = signals.iloc[-1]
        if last['signal_change'] > 0:
            return {'action': 'buy', 'price': last['close'],
                    'K': round(last['K'], 2), 'D': round(last['D'], 2), 'J': round(last['J'], 2)}
        elif last['signal_change'] < 0:
            return {'action': 'sell', 'price': last['close'],
                    'K': round(last['K'], 2), 'D': round(last['D'], 2), 'J': round(last['J'], 2)}
        return {'action': 'hold', 'price': last['close'],
                'K': round(last['K'], 2), 'D': round(last['D'], 2), 'J': round(last['J'], 2)}
