# A股量化交易模拟系统

基于akshare的A股量化交易模拟系统，支持回测、信号分析、模拟交易、持续监控和飞书推送。

**⚠️ 免责声明：本系统为模拟/纸盘交易，不涉及真实资金，所有信号仅供参考，不构成投资建议。**

---

## 目录结构

```
stock_quant/
├── config.json              # 配置文件
├── requirements.txt         # Python依赖
├── main.py                  # 主入口CLI
├── monitor.py               # 监控+飞书推送
├── run_monitor.py           # 监控守护进程
├── backtester.py            # 回测引擎
├── simulator.py             # 模拟交易引擎
├── data_fetcher.py          # 数据获取（akshare + mock降级）
├── qmt_integration.md       # QMT/PTrade实盘集成研究
├── strategies/
│   ├── __init__.py
│   ├── ma_cross.py          # 双均线交叉策略
│   ├── macd.py              # MACD策略
│   ├── rsi.py               # RSI超买超卖策略
│   ├── bollinger.py         # 布林带策略
│   └── kdj.py               # KDJ随机指标策略
├── data/                    # 数据缓存 & 持仓状态
└── logs/                    # 日志
```

---

## 安装

```bash
cd /root/.openclaw/workspace/stock_quant

# 使用venv（推荐）
python3 -m venv .venv
source .venv/bin/activate
pip install akshare pandas numpy requests schedule

# 或直接使用系统Python
pip3 install akshare pandas numpy requests schedule
```

---

## 配置

编辑 `config.json`：

```json
{
  "portfolio": {
    "initial_cash": 1000000,
    "positions": {}
  },
  "stocks": ["688318", "688210", "603220", "600255", "301236", "515980"],
  "monitor": {
    "enabled": true,
    "interval_seconds": 300,
    "push_on_action_only": true,
    "feishu_webhook": ""
  },
  "strategies": {
    "ma_cross": {"short_ma": 5, "long_ma": 20},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "rsi": {"period": 14, "oversold": 30, "overbought": 70},
    "bollinger": {"period": 20, "std_dev": 2},
    "kdj": {"n": 9, "m1": 3, "m2": 3}
  },
  "default_strategy": "ma_cross"
}
```

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `portfolio.initial_cash` | 初始资金（默认100万） |
| `stocks` | 关注的股票代码列表 |
| `monitor.enabled` | 是否启用监控 |
| `monitor.interval_seconds` | 监控检查间隔（秒） |
| `monitor.push_on_action_only` | 仅推送有动作的信号（买/卖），不推送持有 |
| `monitor.feishu_webhook` | 飞书Webhook地址（可选） |
| `strategies.*` | 各策略的参数配置 |
| `default_strategy` | 默认策略 |

---

## 使用方法

### 前置准备

```bash
cd /root/.openclaw/workspace/stock_quant
source .venv/bin/activate
```

### 查看模拟盘状态

```bash
.venv/bin/python3 main.py status
```

### 列出所有可用策略

```bash
.venv/bin/python3 main.py strategies
```

### 分析股票信号

```bash
# 使用默认策略分析所有股票
.venv/bin/python3 main.py analyze

# 指定策略分析
.venv/bin/python3 main.py analyze --strategy rsi
.venv/bin/python3 main.py analyze --strategy bollinger
.venv/bin/python3 main.py analyze --strategy kdj
.venv/bin/python3 main.py analyze --strategy macd
.venv/bin/python3 main.py analyze --strategy ma_cross
```

### 回测策略

```bash
# 默认回测120天
.venv/bin/python3 main.py backtest --code 688318

# 指定策略和天数
.venv/bin/python3 main.py backtest --code 688318 --strategy rsi --days 60
.venv/bin/python3 main.py backtest --code 688318 --strategy bollinger --days 90
.venv/bin/python3 main.py backtest --code 688318 --strategy kdj --days 120

# 指定初始资金
.venv/bin/python3 main.py backtest --code 688318 --strategy macd --cash 500000
```

### 模拟买入

```bash
.venv/bin/python3 main.py buy --code 688318 --price 100.0 --shares 100
```

### 模拟卖出

```bash
.venv/bin/python3 main.py sell --code 688318 --price 110.0 --shares 100
```

### 持续监控

```bash
# 前台运行（Ctrl+C停止）
.venv/bin/python3 main.py monitor

# 后台运行守护进程
.venv/bin/python3 run_monitor.py &
```

---

## 策略说明

### 1. ma_cross - 双均线交叉策略
- **原理**：短期均线上穿长期均线（金叉）买入，死叉卖出
- **参数**：`short_ma`（短期均线，默认5）, `long_ma`（长期均线，默认20）

### 2. macd - MACD策略
- **原理**：MACD柱状图由负转正（金叉）买入，由正转负（死叉）卖出
- **参数**：`fast`（快线周期，默认12）, `slow`（慢线周期，默认26）, `signal`（信号线周期，默认9）

### 3. rsi - RSI超买超卖策略
- **原理**：RSI<30超卖区买入，RSI>70超买区卖出
- **参数**：`period`（RSI周期，默认14）, `oversold`（超卖线，默认30）, `overbought`（超买线，默认70）

### 4. bollinger - 布林带策略
- **原理**：价格触及布林带下轨买入，触及上轨卖出
- **参数**：`period`（周期，默认20）, `std_dev`（标准差倍数，默认2）

### 5. kdj - KDJ随机指标策略
- **原理**：K上穿D（金叉）且J<50买入，K下穿D（死叉）且J>50卖出
- **参数**：`n`（RSV周期，默认9）, `m1`（K周期，默认3）, `m2`（D周期，默认3）

---

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    main.py (CLI)                    │
├──────────┬──────────┬──────────┬──────────┬────────┤
│  status  │ analyze  │ backtest │ buy/sell │monitor │
├──────────┴──────────┴──────────┴──────────┴────────┤
│                                                     │
│  data_fetcher.py  ←── akshare + mock降级             │
│       ↓                                             │
│  strategies/   ←── ma_cross, macd, rsi, bollinger   │
│       ↓                                             │
│  backtester.py  ←── 历史回测                        │
│  simulator.py   ←── 纸盘交易                        │
│  monitor.py     ←── 信号监控 + 飞书推送             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 飞书推送配置

1. 在飞书群中添加"自定义机器人"
2. 复制Webhook地址
3. 将地址填入 `config.json` 中的 `monitor.feishu_webhook`
4. 启用后，每次检测到买/卖信号会自动推送

---

## 数据说明

- **数据来源**：akshare（东方财富/腾讯等免费数据源）
- **降级机制**：网络不可用时自动切换到Mock数据（用于演示）
- **缓存**：已获取的数据缓存在 `data/` 目录，180天内不重复获取

---

## 注意事项

1. 本系统为**模拟/纸盘**，不涉及真实交易
2. 所有交易信号仅供参考，不构成投资建议
3. 实盘交易请通过QMT/PTrade等正规渠道（参见 `qmt_integration.md`）
4. 建议在充分回测验证后再进行模拟盘实操

---

## 故障排查

### 数据获取失败
- 检查网络连接
- akshare服务可能临时不可用，稍后重试
- 系统会自动降级到Mock数据，不影响基本功能

### 飞书推送失败
- 确认Webhook地址正确
- 飞书机器人可能被群管理员禁用
- 检查群机器人安全设置

### 策略报错
- 确认策略名称正确：`ma_cross`, `macd`, `rsi`, `bollinger`, `kdj`
- 确认参数在合理范围内
