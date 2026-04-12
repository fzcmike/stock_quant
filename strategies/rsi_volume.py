"""
RSI + 成交量组合策略
原理：RSI超卖 + 成交量放大 = 买入信号；RSI超买 = 卖出信号
"""
import pandas as pd
import numpy as np

class RSIVolumeStrategy:
    name = "RSI+成交量策略"

    def __init__(self, rsi_period=14, oversold=35, overbought=70, vol_threshold=1.3):
        self.rsi_period = rsi_period
        self.oversold = oversold    # 超卖阈值
        self.overbought = overbought  # 超买阈值
        self.vol_threshold = vol_threshold  # 成交量放大倍数

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 计算RSI
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        
        # 5日均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        
        # 成交量均线
        df['vol_ma5'] = df['volume'].rolling(window=5).mean()
        df['vol_ratio'] = df['volume'] / df['vol_ma5']
        
        # 信号
        df['signal'] = 0
        
        # 买入：RSI<超卖阈值 + 价格在MA5上方 + 成交量放大
        buy_cond = (df['rsi'] < self.oversold) & (df['close'] > df['ma5']) & (df['vol_ratio'] > self.vol_threshold)
        df.loc[buy_cond, 'signal'] = 1
        
        # 卖出：RSI>超买阈值 或 价格跌破MA5
        sell_cond = (df['rsi'] > self.overbought) | (df['close'] < df['ma5'])
        df.loc[sell_cond & (df['rsi'] > 50), 'signal'] = -1
        
        # 只在信号变化时产生交易信号（signal_change用于检测交叉点）
        df['signal_change'] = df['signal'].diff()

        return df[['date', 'close', 'rsi', 'ma5', 'signal', 'signal_change']].dropna()

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
                'reason': f"RSI({last['rsi']:.1f})超卖+放量"
            }
        elif last['signal'] == -1:
            return {
                'action': 'sell',
                'price': last['close'],
                'reason': f"RSI({last['rsi']:.1f})超买"
            }
        return {'action': 'hold', 'price': None}
