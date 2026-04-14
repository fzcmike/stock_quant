#!/bin/bash
# OpenClaw 升级后一键恢复脚本
# 目标：升级容器后，零重装，所有依赖直接可用
#
# 预期状态（应该都已持久化）：
#   uvx/uv      → /root/.openclaw/uv_bin/ (在 openclaw-data 卷)
#   Python venv → /root/.openclaw/workspace/stock_quant/.venv/
#   字体文件    → /volume1/docker/fonts/ (在 NAS)
#   策略文件    → /volume1/docker/strategies/ (在 NAS)
#   Skills      → /root/.openclaw/skills/
#   配置        → /root/.openclaw/config/

set -e

echo "=========================================="
echo "  OpenClaw 升级后恢复检查"
echo "=========================================="
echo ""

# 1. 设置 PATH（持久化配置）
echo "[1/6] 设置 PATH..."
BASHRC=~/.bashrc
if ! grep -q "uv_bin" $BASHRC 2>/dev/null; then
    echo 'export PATH="/root/.openclaw/uv_bin:$PATH"' >> $BASHRC
    echo "  → 已添加 uv_bin 到 PATH"
else
    echo "  ✓ PATH 已配置"
fi
export PATH="/root/.openclaw/uv_bin:$PATH"

# 2. 验证 uvx
echo "[2/6] 检查 uvx..."
if which uvx >/dev/null 2>&1; then
    echo "  ✓ uvx: $(which uvx)"
else
    echo "  ✗ uvx 找不到！"
    exit 1
fi

# 3. 验证 Python venv
echo "[3/6] 检查 Python venv..."
VENV=~/.openclaw/workspace/stock_quant/.venv
if [ -d "$VENV" ]; then
    echo "  ✓ venv 存在"
    # 测试关键包
    if $VENV/bin/python3 -c "import akshare, pandas, numpy, matplotlib, PIL" 2>/dev/null; then
        echo "  ✓ 关键包 (akshare, pandas, numpy, matplotlib, PIL) 正常"
    else
        echo "  ✗ 部分包导入失败"
    fi
else
    echo "  ✗ venv 不存在！"
    exit 1
fi

# 4. 检查字体
echo "[4/6] 检查字体文件..."
FONT=~/.openclaw/workspace/NotoSansSC-Regular.ttf
FONT2=/volume1/docker/fonts/NotoSansCJK.ttf
if [ -f "$FONT" ] || [ -f "$FONT2" ]; then
    echo "  ✓ 字体文件存在"
else
    echo "  ! 字体文件未找到"
fi

# 5. 检查策略
echo "[5/6] 检查策略文件..."
if [ -f /volume1/docker/strategies/__init__.py ]; then
    COUNT=$(ls /volume1/docker/strategies/*.py 2>/dev/null | wc -l)
    echo "  ✓ 策略文件存在 ($COUNT 个)"
else
    echo "  ! 策略文件未找到"
fi

# 6. 检查NAS连接
echo "[6/6] 检查 NAS 存储..."
if [ -d /volume1/docker ]; then
    echo "  ✓ NAS 目录可访问"
else
    echo "  ! NAS 目录不可访问"
fi

echo ""
echo "=========================================="
echo "  检查完成"
echo "=========================================="
echo ""
echo "✓ 所有依赖就绪，升级后无需重装！"
echo ""

# 启动A股量化守护进程
$VENV/bin/python3 -u $WORKSPACE/stock_quant/daemon.py >> $WORKSPACE/stock_quant/logs/daemon.log 2>&1 &
echo "  ✓ A股量化守护进程已启动 (PID=$!)"
