"""
双均线交叉策略
买入信号：短期均线上穿长期均线（金叉）
卖出信号：短期均线上穿长期均线（死叉）
"""
import pandas as pd
import numpy as np

class MACrossStrategy:
    name = "双均线交叉策略"

    def __init__(self, short_ma=5, long_ma=20):
        self.short_ma = short_ma
        self.long_ma = long_ma

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        df['ma_short'] = df['close'].rolling(window=self.short_ma).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_ma).mean()

        # 金叉/死叉信号
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1  # 买入
        df.loc[df['ma_short'] <= df['ma_long'], 'signal'] = -1  # 卖出

        # 只在变化时产生信号（signal_change用于检测交叉点）
        df['signal_change'] = df['signal'].diff()
        # signal保持原值（1买入/-1卖出/0持有），signal_change标记是否发生变化

        return df[['date', 'close', 'ma_short', 'ma_long', 'signal', 'signal_change']].dropna()

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        """获取最新信号"""
        signals = self.generate_signals(data)
        if signals.empty:
            return {'action': 'hold', 'price': None}

        last = signals.iloc[-1]
        prev = signals.iloc[-2] if len(signals) > 1 else None

        if last['signal_change'] > 0:
            return {'action': 'buy', 'price': last['close'], 'date': str(last['date'])}
        elif last['signal_change'] < 0:
            return {'action': 'sell', 'price': last['close'], 'date': str(last['date'])}
        else:
            return {'action': 'hold', 'price': last['close'], 'date': str(last['date'])}
