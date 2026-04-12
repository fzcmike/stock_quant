#!/usr/bin/env python3
"""
A股量化交易模拟系统 - 主入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import argparse
import json
import time
from datetime import datetime
from simulator import StockSimulator
from monitor import QuantMonitor
from backtester import Backtester
from data_fetcher import get_stock_daily
from strategies import list_strategies, get_strategy

def cmd_status(args):
    sim = StockSimulator()
    status = sim.get_status()
    print(f"\n{'='*50}")
    print(f"📊 模拟盘状态 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    print(f"💰 现金: ¥{status['cash']:,.2f}")
    print(f"📦 持仓数: {len(status['positions'])}")
    print(f"📝 交易记录: {status['history_count']}笔")

    if status['positions']:
        print(f"\n持仓明细:")
        for code, pos in status['positions'].items():
            print(f"  {code}: {pos['shares']}股 @ ¥{pos['avg_cost']:.2f}")

    history = sim.get_history(10)
    if history:
        print(f"\n最近交易:")
        for h in history:
            print(f"  {h['time'][:19]} | {h['action']} | {h['code']} | {h['price']} | {h.get('shares', '')}股")
    print()

def cmd_analyze(args):
    monitor = QuantMonitor()
    strategy_name = args.strategy or monitor.strategy_name

    # 如果指定了策略，覆盖monitor的策略
    if args.strategy:
        monitor.strategy_name = args.strategy

    report = monitor.run_once(push=False)
    print(report)

def cmd_backtest(args):
    code = args.code
    strategy_name = args.strategy or 'ma_cross'

    print(f"回测 {code} 使用 {strategy_name} 策略...")

    df = get_stock_daily(code, args.days or 120)
    if df.empty:
        print("获取数据失败")
        return

    try:
        # 从config获取策略参数
        from strategies import get_strategy
        import json as jsonmod
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            config = jsonmod.load(f)
        strategy_params = config.get('strategies', {}).get(strategy_name, {})
        strategy = get_strategy(strategy_name, **strategy_params)
        signals = strategy.generate_signals(df)
    except Exception as e:
        print(f"策略加载失败: {e}")
        return

    bt = Backtester(initial_cash=args.cash or 1000000)
    result = bt.run(df, signals, code)

    print(f"\n{'='*50}")
    print(f"回测结果: {code}")
    print(f"{'='*50}")
    print(f"策略: {strategy.name}")
    print(f"初始资金: ¥{result['initial_cash']:,.2f}")
    print(f"最终资产: ¥{result['final_value']:,.2f}")
    print(f"总收益率: {result['total_return']:+.2f}%")
    print(f"总交易次数: {result['total_trades']}")

    trades = bt.get_trades()
    if trades:
        print(f"\n交易记录:")
        for t in trades:
            print(f"  {str(t['date'])[:10]} | {t['action']} | {t['code']} | {t['price']} | {t['shares']}股")

def cmd_buy(args):
    sim = StockSimulator()
    result = sim.buy(args.code, args.price, args.shares)
    if result['success']:
        print(f"✅ 买入成功: {args.code} {result['shares']}股 @ ¥{args.price}")
    else:
        print(f"❌ 买入失败: {result['reason']}")

def cmd_sell(args):
    sim = StockSimulator()
    result = sim.sell(args.code, args.price, args.shares)
    if result['success']:
        print(f"✅ 卖出成功: {args.code} {result['shares']}股 @ ¥{args.price}")
    else:
        print(f"❌ 卖出失败: {result['reason']}")

def cmd_monitor(args):
    monitor = QuantMonitor()
    interval = monitor.interval_seconds
    print(f"{'='*50}")
    print(f"🚀 启动A股量化监控守护进程")
    print(f"{'='*50}")
    print(f"检查间隔: {interval}秒")
    print(f"飞书推送: {'已配置' if monitor.feishu_webhook else '未配置（仅本地输出）'}")
    print(f"动作推送: {'仅动作信号' if monitor.push_on_action_only else '完整报告'}")
    print(f"{'='*50}")
    print("按 Ctrl+C 停止\n")

    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 检查信号...")
        monitor.run_once(push=True)
        time.sleep(interval)

def cmd_strategies(args):
    strategies = list_strategies()
    print(f"\n{'='*50}")
    print(f"📈 可用策略列表")
    print(f"{'='*50}")
    for name, display_name in strategies.items():
        print(f"  {name:12s} - {display_name}")
    print(f"\n共 {len(strategies)} 个策略")
    print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A股量化交易模拟系统')
    subparsers = parser.add_subparsers(dest='cmd')

    # status
    subparsers.add_parser('status', help='查看模拟盘状态')

    # analyze
    p_analyze = subparsers.add_parser('analyze', help='分析股票信号')
    p_analyze.add_argument('--strategy', help='指定策略 (ma_cross/macd/rsi/bollinger/kdj)')

    # strategies
    subparsers.add_parser('strategies', help='列出所有可用策略')

    # monitor
    subparsers.add_parser('monitor', help='持续监控模式')

    # backtest
    p_backtest = subparsers.add_parser('backtest', help='回测策略')
    p_backtest.add_argument('--code', required=True, help='股票代码')
    p_backtest.add_argument('--strategy', help='策略名称')
    p_backtest.add_argument('--days', type=int, help='回测天数')
    p_backtest.add_argument('--cash', type=float, help='初始资金')

    # buy
    p_buy = subparsers.add_parser('buy', help='买入')
    p_buy.add_argument('--code', required=True, help='股票代码')
    p_buy.add_argument('--price', type=float, required=True, help='价格')
    p_buy.add_argument('--shares', type=int, help='股数')

    # sell
    p_sell = subparsers.add_parser('sell', help='卖出')
    p_sell.add_argument('--code', required=True, help='股票代码')
    p_sell.add_argument('--price', type=float, required=True, help='价格')
    p_sell.add_argument('--shares', type=int, help='股数')

    args = parser.parse_args()

    if args.cmd == 'status':
        cmd_status(args)
    elif args.cmd == 'analyze':
        cmd_analyze(args)
    elif args.cmd == 'strategies':
        cmd_strategies(args)
    elif args.cmd == 'monitor':
        cmd_monitor(args)
    elif args.cmd == 'backtest':
        cmd_backtest(args)
    elif args.cmd == 'buy':
        cmd_buy(args)
    elif args.cmd == 'sell':
        cmd_sell(args)
    else:
        parser.print_help()
