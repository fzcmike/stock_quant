"""
回测引擎
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict
import json
import os

class Backtester:
    def __init__(self, initial_cash=1000000, commission=0.0003):
        self.initial_cash = initial_cash
        self.commission = commission
        self.trades = []
        self.positions = {}  # {code: {'shares': int, 'avg_cost': float}}

    def run(self, data: pd.DataFrame, signals: pd.DataFrame, code: str) -> Dict:
        """运行回测"""
        cash = self.initial_cash
        shares = 0
        records = []

        for _, row in signals.iterrows():
            date = row['date']
            price = row['close']
            action = row.get('signal_change', 0)

            if action > 0 and cash >= price * 100:  # 买入，至少买100股
                buy_shares = int(cash / price / 100) * 100
                cost = buy_shares * price * (1 + self.commission)
                if cost <= cash:
                    cash -= cost
                    shares += buy_shares
                    self.trades.append({
                        'date': date, 'code': code, 'action': 'buy',
                        'price': price, 'shares': buy_shares, 'cost': cost
                    })

            elif action < 0 and shares > 0:  # 卖出
                revenue = shares * price * (1 - self.commission)
                cash += revenue
                self.trades.append({
                    'date': date, 'code': code, 'action': 'sell',
                    'price': price, 'shares': shares, 'revenue': revenue
                })
                shares = 0

        # 计算最终资产
        if shares > 0 and not signals.empty:
            final_price = signals.iloc[-1]['close']
            final_value = cash + shares * final_price
        else:
            final_value = cash

        return {
            'initial_cash': self.initial_cash,
            'final_value': final_value,
            'total_return': (final_value - self.initial_cash) / self.initial_cash * 100,
            'total_trades': len(self.trades),
            'final_cash': cash,
            'final_shares': shares
        }

    def get_trades(self) -> List[Dict]:
        return self.trades
