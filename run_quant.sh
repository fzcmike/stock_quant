#!/bin/bash
# A股量化交易定时任务wrapper - 只在交易时间内执行

PYTHON="/root/.openclaw/workspace/stock_quant/.venv/bin/python3"
SCRIPT_DIR="/root/.openclaw/workspace/stock_quant"
LOG="$SCRIPT_DIR/logs/cron量化.log"

# 北京时间判断是否在交易时间
TZ=Asia/Shanghai
export TZ

HOUR=$(date +%H)
MIN=$(date +%M)
DAY=$(date +%w)  # 0=周日,1=周一...

# 周一到周五
if [ "$DAY" -ge 1 ] && [ "$DAY" -le 5 ]; then
    # 上午 9:30-11:30
    if [ "$HOUR" -eq 9 ] && [ "$MIN" -ge 30 ] || [ "$HOUR" -eq 10 ] || [ "$HOUR" -eq 11 ]; then
        IN_TRADE_TIME=true
    # 下午 13:00-15:00
    elif [ "$HOUR" -ge 13 ] && [ "$HOUR" -le 14 ]; then
        IN_TRADE_TIME=true
    else
        IN_TRADE_TIME=false
    fi
else
    IN_TRADE_TIME=false
fi

if [ "$IN_TRADE_TIME" = true ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行..." >> $LOG
    cd $SCRIPT_DIR
    $PYTHON -c "
import sys; sys.path.insert(0, '.')
from monitor import QuantMonitor
m = QuantMonitor()
m.run_once(push=False)
" >> $LOG 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行完成" >> $LOG
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 非交易时间，跳过" >> $LOG
fi
