"""
监控模块 - 读取策略信号，生成交易建议并推送
支持多策略配置、动作信号推送飞书
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from datetime import datetime, timedelta
from typing import Dict, List
from simulator import StockSimulator
from data_fetcher import get_stock_daily, get_realtime_quote
import requests

class QuantMonitor:
    def __init__(self, config_path: str = None):
        base_dir = os.path.dirname(__file__)
        self.config_path = config_path or os.path.join(base_dir, 'config.json')
        self.load_config()

        self.simulator = StockSimulator(self.config_path)
        self.default_strategy = self.config.get('default_strategy', 'kdj')
        self.per_stock_strategy = self.config.get('per_stock_strategy', {})
        self.strategy_name = self.default_strategy

        # 从config读取监控配置
        monitor_cfg = self.config.get('monitor', {})
        self.enabled = monitor_cfg.get('enabled', True)
        self.interval_seconds = monitor_cfg.get('interval_seconds', 300)
        self.push_on_action_only = monitor_cfg.get('push_on_action_only', True)
        self.feishu_webhook = monitor_cfg.get('feishu_webhook', '')

    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

    def get_strategy_for_stock(self, code: str) -> str:
        """获取单个股票适用的策略（优先per-stock，其次默认）"""
        return self.per_stock_strategy.get(code, self.default_strategy)

    def get_strategy_params(self, strategy_name: str) -> dict:
        """从配置中获取策略参数"""
        strategy_configs = self.config.get('strategies', {})
        return strategy_configs.get(strategy_name, {})

    def analyze_stock(self, code: str, days: int = 60) -> Dict:
        """分析单只股票（使用配置中的策略参数）"""
        df = get_stock_daily(code, days)
        if df.empty:
            return {'code': code, 'error': '获取数据失败'}

        latest_price = df.iloc[-1]['close']
        # 每个股票用自己的策略
        strategy_name = self.get_strategy_for_stock(code)

        try:
            from strategies import get_strategy
            params = self.get_strategy_params(strategy_name)
            strategy = get_strategy(strategy_name, **params)
            signal = strategy.get_latest_signal(df)
        except Exception as e:
            # 降级：使用简单均线交叉
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma5_prev = df['close'].rolling(5).mean().iloc[-2]
            ma20_prev = df['close'].rolling(20).mean().iloc[-2]

            if ma5 > ma20 and ma5_prev <= ma20_prev:
                action = 'buy'
            elif ma5 < ma20 and ma5_prev >= ma20_prev:
                action = 'sell'
            else:
                action = 'hold'

            signal = {'action': action, 'price': latest_price}

        return {
            'code': code,
            'latest_price': latest_price,
            'signal': signal,
            'strategy': strategy_name
        }

    def analyze_all(self) -> Dict:
        """分析所有配置的股票"""
        results = {}
        stocks = self.config.get('stocks', [])

        for code in stocks:
            results[code] = self.analyze_stock(code)

        return results

    def check_signals(self) -> Dict:
        """检查所有信号，返回需要操作的"""
        analysis = self.analyze_all()
        signals = {}

        for code, result in analysis.items():
            if 'error' in result:
                continue
            sig = result['signal']
            if sig['action'] != 'hold':
                signals[code] = result

        return signals

    def generate_report(self, action_signals_only: bool = False) -> str:
        """生成分析报告
        
        Args:
            action_signals_only: 是否只显示需要操作的信号
        """
        analysis = self.analyze_all()
        
        # 北京时间
        now_bj = datetime.utcnow() + timedelta(hours=8)
        
        lines = [
            f"📊 A股量化信号报告",
            f"⏰ {now_bj.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)",
            f"📈 全局策略: {self.default_strategy}",
        ]

        status = self.simulator.get_status()
        lines.append(f"💰 模拟盘状态:")
        lines.append(f"   现金: ¥{status['cash']:,.2f}")
        lines.append(f"   持仓数: {len(status['positions'])}")
        lines.append(f"   交易记录: {status['history_count']}笔")
        lines.append(f"")

        if action_signals_only:
            lines.append(f"🚨 动作信号:")
            has_action = False
            for code, result in analysis.items():
                if 'error' in result:
                    continue
                sig = result['signal']
                if sig['action'] == 'hold':
                    continue
                has_action = True
                price = result['latest_price']
                strat = result.get('strategy', self.default_strategy)

                if sig['action'] == 'buy':
                    emoji = '🟢'
                    action_text = '买入'
                else:
                    emoji = '🔴'
                    action_text = '卖出'

                extras = ', '.join(f"{k}={v}" for k, v in sig.items() if k not in ('action', 'price', 'date'))
                lines.append(f"   {code}: {emoji} {action_text} @ ¥{price:.2f} [策略:{strat}] {extras}")

                if code in status['positions']:
                    pos = status['positions'][code]
                    pnl = (price - pos['avg_cost']) / pos['avg_cost'] * 100
                    lines.append(f"      持仓: {pos['shares']}股, 成本¥{pos['avg_cost']:.2f}, 盈亏{pnl:+.1f}%")

            if not has_action:
                lines.append(f"   暂无动作信号")
        else:
            lines.append(f"📋 个股信号:")
            for code, result in analysis.items():
                if 'error' in result:
                    lines.append(f"   {code}: ❌ {result['error']}")
                    continue

                sig = result['signal']
                price = result['latest_price']
                strat = result.get('strategy', self.default_strategy)

                if sig['action'] == 'buy':
                    emoji = '🟢'
                    action_text = '买入'
                elif sig['action'] == 'sell':
                    emoji = '🔴'
                    action_text = '卖出'
                else:
                    emoji = '⚪'
                    action_text = '持有'

                lines.append(f"   {code}: {emoji} {action_text} @ ¥{price:.2f} [策略:{strat}]")

                # 如果有持仓，显示成本和盈亏
                if code in status['positions']:
                    pos = status['positions'][code]
                    pnl = (price - pos['avg_cost']) / pos['avg_cost'] * 100
                    lines.append(f"      持仓: {pos['shares']}股, 成本¥{pos['avg_cost']:.2f}, 盈亏{pnl:+.1f}%")

        return '\n'.join(lines)

    def push_to_feishu(self, message: str) -> bool:
        """推送到飞书"""
        webhook = self.feishu_webhook or self.config.get('feishu_webhook', '')
        if not webhook:
            print("未配置飞书webhook，跳过推送")
            return False

        try:
            resp = requests.post(webhook, json={
                "msg_type": "text",
                "content": {"text": message}
            }, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"推送失败: {e}")
            return False

    def run_once(self, push: bool = True) -> str:
        """运行一次分析：检查信号 + 执行交易 + 生成报告"""
        action_signals = self.check_signals()
        
        # 执行交易（模拟自动下单）
        executed_trades = []
        for code, result in action_signals.items():
            sig = result['signal']
            price = result['latest_price']
            
            if sig['action'] == 'buy':
                # 先检查是否已持有这只股票
                status = self.simulator.get_status()
                if code in status['positions']:
                    print(f"[跳过] {code} 已持仓，无需买入")
                    continue
                
                # 用一半资金买入（留一半现金防风险）
                trade_result = self.simulator.buy(
                    code=code,
                    price=price,
                    shares=None  # simulator内部自动计算
                )
                if trade_result['success']:
                    trade_result['exec_price'] = price
                    executed_trades.append(trade_result)
                    print(f"[成交] 买入 {code} {trade_result['shares']}股 @ ¥{price:.2f}")
                else:
                    print(f"[拒绝] 买入 {code} 失败: {trade_result['reason']}")
            
            elif sig['action'] == 'sell':
                # 全部卖出
                trade_result = self.simulator.sell(
                    code=code,
                    price=price,
                    shares=None  # 全部卖出
                )
                if trade_result['success']:
                    trade_result['exec_price'] = price
                    executed_trades.append(trade_result)
                    print(f"[成交] 卖出 {code} {trade_result['shares']}股 @ ¥{price:.2f}")
                else:
                    print(f"[拒绝] 卖出 {code} 失败: {trade_result['reason']}")
        
        # 生成报告
        if self.push_on_action_only and action_signals:
            report = self.generate_report(action_signals_only=True)
            print(report)
            if push:
                self.push_to_feishu(report)
        elif not self.push_on_action_only:
            report = self.generate_report()
            print(report)
            if push:
                self.push_to_feishu(report)
        else:
            report = "无动作信号，跳过推送"
            print(report)

        return report
