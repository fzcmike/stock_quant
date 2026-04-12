#!/usr/bin/env python3
"""
持续运行的监控守护进程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
import signal
import atexit
from monitor import QuantMonitor

running = True

def signal_handler(signum, frame):
    global running
    print("\n收到停止信号，正在退出...")
    running = False

def cleanup():
    print("监控已停止")

if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)

    monitor = QuantMonitor()
    interval = monitor.interval_seconds

    print(f"=" * 50)
    print(f"🚀 A股量化监控守护进程启动")
    print(f"=" * 50)
    print(f"检查间隔: {interval}秒")
    print(f"飞书推送: {'已配置' if monitor.feishu_webhook else '未配置（仅本地输出）'}")
    print(f"动作推送: {'仅动作信号' if monitor.push_on_action_only else '完整报告'}")
    print(f"=" * 50)
    print("按 Ctrl+C 停止")
    print()

    # 先运行一次
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 首次检查...")
    monitor.run_once(push=True)

    # 守护循环
    while running:
        time.sleep(interval)
        if running:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 再次检查...")
            monitor.run_once(push=True)
