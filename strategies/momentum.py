"""
动量选股策略
原理：追强势股，过去N日涨幅最高的股票优先买入
"""
import pandas as pd
import numpy as np

class MomentumStrategy:
    name = "动量选股策略"

    def __init__(self, short_window=10, long_window=20, min_momentum=5):
        self.short_window = short_window
        self.long_window = long_window
        self.min_momentum = min_momentum  # 最小动量阈值

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 计算动量（价格变化率）
        df['momentum'] = (df['close'] / df['close'].shift(self.short_window) - 1) * 100
        df['momentum_long'] = (df['close'] / df['close'].shift(self.long_window) - 1) * 100
        
        # 5日均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        
        # 成交量均线
        df['vol_ma5'] = df['volume'].rolling(window=5).mean()
        df['vol_ratio'] = df['volume'] / df['vol_ma5']
        
        # 动量 > 阈值 且 价格在MA5上方 → 买入
        df['signal'] = 0
        df.loc[(df['momentum'] > self.min_momentum) & 
               (df['close'] > df['ma5']) &
               (df['vol_ratio'] > 1.2), 'signal'] = 1
        
        # 动量转负 或 价格跌破MA5 → 卖出
        df.loc[(df['momentum'] < 0) | 
               (df['close'] < df['ma5']), 'signal'] = -1
        
        df['signal_change'] = df['signal'].diff()
        df.loc[df['signal_change'] == 0, 'signal'] = 0
        
        return df[['date', 'close', 'momentum', 'ma5', 'signal', 'signal_change']].dropna()

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        """获取最新信号"""
        signals = self.generate_signals(data)
        if signals.empty:
            return {'action': 'hold', 'price': None}
        
        last = signals.iloc[-1]
        if last['signal'] == 1:
            return {
                'action': 'buy',
                'price': last['close'],
                'reason': f"动量({last['momentum']:.1f}%)>+阈值"
            }
        elif last['signal'] == -1:
            return {
                'action': 'sell',
                'price': last['close'],
                'reason': "动量减弱"
            }
        return {'action': 'hold', 'price': None}
