#!/bin/bash
# 启动 Llama Server (Qwen 2B 多模态)

BASE_DIR=$(dirname "$0")
BIN_PATH="$BASE_DIR/../llama-cpp/llama-server"
MODEL_PATH="$BASE_DIR/../2B-new/Qwen3.5-2B.Q4_K_M.gguf"
MMPROJ_PATH="$BASE_DIR/../2B-new/mmproj-BF16.gguf"

# 检查可执行文件 (Linux 版本通常没有 .exe)
if [ ! -f "$BIN_PATH" ]; then
    BIN_PATH="$BASE_DIR/../llama-cpp/llama-server.exe" # 某些子系统也可能直接用 exe
fi

echo "正在启动本地 Llama Server..."
echo "模型: $MODEL_PATH"

"$BIN_PATH" -m "$MODEL_PATH" --mmproj "$MMPROJ_PATH" -ngl -1 --host 0.0.0.0 --port 8080 -c 4096
