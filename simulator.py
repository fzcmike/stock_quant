"""
模拟交易引擎 - 纸盘交易
"""
import json
import os
from datetime import datetime
from typing import Dict, List

class StockSimulator:
    def __init__(self, config_path: str = None):
        self.base_dir = os.path.dirname(__file__)
        self.config_path = config_path or os.path.join(self.base_dir, 'config.json')
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.logs_dir = os.path.join(self.base_dir, 'logs')

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.load_config()
        self.load_state()

    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

    def load_state(self):
        state_file = os.path.join(self.data_dir, 'portfolio_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                'cash': self.config['portfolio']['initial_cash'],
                'positions': {},
                'history': [],
                'last_update': datetime.now().isoformat()
            }

    def save_state(self):
        state_file = os.path.join(self.data_dir, 'portfolio_state.json')
        self.state['last_update'] = datetime.now().isoformat()
        with open(state_file, 'w') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def buy(self, code: str, price: float, shares: int = None) -> Dict:
        """买入"""
        if shares is None:
            shares = int(self.state['cash'] / price / 100) * 100

        cost = shares * price
        if cost > self.state['cash']:
            return {'success': False, 'reason': '资金不足'}

        self.state['cash'] -= cost

        if code in self.state['positions']:
            old = self.state['positions'][code]
            total_shares = old['shares'] + shares
            avg_cost = (old['avg_cost'] * old['shares'] + price * shares) / total_shares
            self.state['positions'][code] = {'shares': total_shares, 'avg_cost': avg_cost}
        else:
            self.state['positions'][code] = {'shares': shares, 'avg_cost': price}

        trade_record = {
            'time': datetime.now().isoformat(),
            'action': 'BUY',
            'code': code,
            'price': price,
            'shares': shares,
            'cost': cost,
            'cash': self.state['cash']
        }
        self.state['history'].append(trade_record)
        self.save_state()

        return {'success': True, **trade_record}

    def sell(self, code: str, price: float, shares: int = None) -> Dict:
        """卖出"""
        if code not in self.state['positions']:
            return {'success': False, 'reason': '无持仓'}

        position = self.state['positions'][code]
        sell_shares = shares or position['shares']

        if sell_shares > position['shares']:
            return {'success': False, 'reason': '持仓不足'}

        revenue = sell_shares * price
        self.state['cash'] += revenue

        remaining = position['shares'] - sell_shares
        if remaining == 0:
            del self.state['positions'][code]
        else:
            self.state['positions'][code]['shares'] = remaining

        trade_record = {
            'time': datetime.now().isoformat(),
            'action': 'SELL',
            'code': code,
            'price': price,
            'shares': sell_shares,
            'revenue': revenue,
            'cash': self.state['cash']
        }
        self.state['history'].append(trade_record)
        self.save_state()

        return {'success': True, **trade_record}

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """计算当前总资产"""
        positions_value = sum(
            pos['shares'] * current_prices.get(code, pos['avg_cost'])
            for code, pos in self.state['positions'].items()
        )
        return self.state['cash'] + positions_value

    def get_status(self) -> Dict:
        return {
            'cash': round(self.state['cash'], 2),
            'positions': self.state['positions'],
            'total_value': None,  # 需要实时价格
            'history_count': len(self.state['history'])
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        return self.state['history'][-limit:]
