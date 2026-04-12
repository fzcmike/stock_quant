# A股量化系统 - 持久化与恢复指南

## 目录结构
```
/root/.openclaw/workspace/stock_quant/    # 工作区（建议持久化到NAS）
├── strategies/                           # 7个量化策略
├── data/                                 # 历史数据
├── logs/                                 # 日志
├── fonts/                                # 中文字体（需单独配置）
└── requirements.txt                      # Python依赖

/volume1/docker/                           # NAS量化目录
├── data/                                 # 持仓状态、模拟交易数据
├── fonts/                                # 思源黑体字体
│   ├── NotoSansCJK.ttf                  # 19MB
│   └── NotoSansCJK-Bold.ttf             # 20MB
├── strategies/                           # 策略文件
└── *.py                                  # 交易脚本
```

## 升级后恢复步骤

### 1. Python依赖
```bash
pip install -r requirements.txt
```

### 2. 字体文件（如丢失）
字体文件在 `/volume1/docker/fonts/`（已持久化）
如需恢复，从备份重新上传 NotoSansCJK.ttf 和 NotoSansCJK-Bold.ttf

### 3. uvx 工具（如丢失）
```bash
pip install uvx
```

### 4. 工作区代码
代码在 OpenClaw workspace（`/root/.openclaw/workspace/stock_quant/`）
建议通过 bind mount 持久化

## Docker 持久化配置建议

在 docker-compose.yml 中添加：
```yaml
volumes:
  - /root/.openclaw/workspace:/root/.openclaw/workspace
  - /volume1/docker/data:/volume1/docker/data
  - /volume1/docker/fonts:/volume1/docker/fonts
```

## NAS目录持久化
- `/volume1/docker/` 已在 NAS 上，重启不丢
- 字体文件在 `/volume1/docker/fonts/`（19MB + 20MB）
- 模拟盘数据在 `/volume1/docker/data/`
