#!/bin/bash
# 升级后恢复脚本 - 恢复字体文件
# 用法: bash setup_persistence.sh

DOCKER_DIR="/volume1/docker"
FONT_DIR="$DOCKER_DIR/fonts"

echo "检查字体文件..."

if [ ! -f "$FONT_DIR/NotoSansCJK.ttf" ]; then
    echo "字体文件缺失，正在恢复..."
    # 字体应该在Docker镜像中已存在，或者通过挂载volume持久化
    # 如果缺失，需要重新上传
    echo "请手动上传字体文件到 $FONT_DIR/"
else
    echo "字体文件存在: $(ls -lh $FONT_DIR/)"
fi

echo "检查数据目录..."
if [ -d "$DOCKER_DIR/data" ]; then
    echo "数据目录存在"
else
    mkdir -p "$DOCKER_DIR/data"
    echo "已创建数据目录"
fi

echo "检查策略文件..."
if [ -f "$DOCKER_DIR/strategies/__init__.py" ]; then
    echo "策略文件存在"
else
    echo "警告: 策略文件缺失，请重新部署"
fi

echo ""
echo "持久化路径:"
echo "  字体: $FONT_DIR/"
echo "  数据: $DOCKER_DIR/data/"
echo "  策略: $DOCKER_DIR/strategies/"
echo "  脚本: $DOCKER_DIR/*.py"
echo ""
echo "建议: 将 $FONT_DIR 和 $DOCKER_DIR/data 挂载为Docker volume"
