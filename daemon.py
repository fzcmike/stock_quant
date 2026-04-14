#!/root/.openclaw/workspace/stock_quant/.venv/bin/python3
"""
A股量化交易守护进程 - 时间感知自动运行
交易时间：周一至周五 9:30-11:30、13:00-15:00
"""
import sys, os, time
sys.path.insert(0, '/root/.openclaw/workspace/stock_quant')
os.environ['TZ'] = 'Asia/Shanghai'
time.tzset()  # 让系统立即应用时区设置

from monitor import QuantMonitor
import signal

RUNNING = True

def signal_handler(sig, frame):
    global RUNNING
    print("收到退出信号，停止监控...")
    RUNNING = False

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def is_trading_time():
    """判断当前是否在交易时间内（北京时间）"""
    import datetime
    # 直接使用北京时间 (UTC+8)
    beijing_tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(beijing_tz)
    weekday = now.weekday()  # 0=周一
    hour = now.hour
    minute = now.minute

    if weekday >= 5:  # 周六、周日
        return False

    # 上午 9:30-11:30
    if hour == 9 and minute >= 30 or hour == 10 or (hour == 11 and minute <= 30):
        return True
    # 下午 13:00-15:00（含15:00）
    if hour >= 13 and hour <= 15:
        return True

    return False

def wait_interval(secs):
    """分段等待，每秒检查一次退出信号"""
    for _ in range(secs):
        if not RUNNING:
            return False
        time.sleep(1)
    return True

print("=" * 50)
print("A股量化交易守护进程启动")
print("交易时间：周一至周五 9:30-11:30、13:00-15:00")
print("=" * 50)

monitor = QuantMonitor()
LOOP_INTERVAL = 300  # 5分钟
last_trade_minute = -1

while RUNNING:
    if is_trading_time():
        current_minute = time.localtime().tm_min
        # 同一分钟内不重复执行
        if current_minute != last_trade_minute:
            print(f"\n[{time.strftime('%H:%M:%S')}] 交易时间，开始检查信号...")
            try:
                result = monitor.run_once(push=False)
                print(result)
            except Exception as e:
                print(f"执行出错: {e}")
            last_trade_minute = current_minute
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 交易中，等待下一轮...")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] 非交易时间，休眠中...")
        last_trade_minute = -1

    if not wait_interval(LOOP_INTERVAL):
        break

print("守护进程已退出")
