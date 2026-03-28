# 仪器读数识别系统

使用 LMStudio 本地部署 Qwen3.5 多模态模型进行仪器读数识别

## 系统架构

使用 LMStudio（OpenAI 兼容 API）本地多模态模型：
- `4b`：多模态读取（默认）
- `2b`：多模态读取（可选）

---

## 快速开始

### 前置条件

- Python 3.8+
- LMStudio 已安装（https://lmstudio.ai/）

### 第一步：环境检查

如果 LMStudio 服务已经运行且模型已经加载，可直接跳过本步骤。

#### 安装 Python 客户端（如果未安装）
```bash
pip install -r requirements.txt
```

### 第二步：启动模型服务（如果未启动）

在 LMStudio 中加载多模态模型，启动本地服务器（默认端口 1234）。

等待模型加载完成后再继续。

### 第三步：读取仪器图片

```bash
python read_instrument.py demo/1.jpg
```

示例输出：
```
仪器类型: electronic_balance
仪器名称: 电子天平/分析天平
读数:
  weight: 12.34 g
置信度: 0.95
```

---

## 相机 TCP 服务

系统支持通过 TCP 协议控制多台相机进行自动拍照和读数识别。

### 功能特点

- 支持 9 台相机同时工作
- TCP 协议触发拍照
- 自动等待拍摄完成
- 图像自动缩放（最长边 500 像素）
- 返回 JSON 格式读数结果

### 启动服务

```bash
# 正常模式
python camera_service.py

# 测试模式（不连接真实相机，使用已有图片）
python camera_service.py --test

# 指定端口
python camera_service.py --port 9999
```

### 使用方式

通过 TCP 连接发送指令，格式为 `XXXX,N`（N 为相机编号，0-8）：

```bash
# 使用 netcat 发送指令（触发第1个相机拍照）
echo "XXXX,0" | nc localhost 8888

# 触发第3个相机
echo "XXXX,2" | nc localhost 8888
```

### 返回格式

成功响应：
```json
{
  "camera_id": 0,
  "timestamp": "2024-03-16T10:30:00",
  "success": true,
  "image_path": "/path/to/image.jpg",
  "instrument_type": "electronic_balance",
  "instrument_name": "电子天平",
  "readings": {
    "weight": "12.34"
  },
  "confidence": 0.95,
  "elapsed_time": 3.5
}
```

失败响应：
```json
{
  "camera_id": 0,
  "success": false,
  "error": "拍照失败: 连接超时"
}
```

---

## 常用命令

```bash
# 批量处理文件夹
python read_instrument.py --dir ./images

# 交互式模式
python read_instrument.py -i

# 指定输出目录
python read_instrument.py image.jpg --output ./results

# 静默模式
python read_instrument.py image.jpg -q

# 关闭可视化
python read_instrument.py image.jpg --no-visual
```

---

## 配置参数

所有参数均可通过环境变量覆盖：

### LMStudio 配置

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `LMSTUDIO_BASE_URL` | `http://127.0.0.1:1234` | LMStudio 服务器地址 |
| `LMSTUDIO_MODEL` | `4b` | 多模态模型名称 |
| `MODEL_TEMPERATURE` | `0.1` | 生成温度 |
| `MODEL_MAX_TOKENS` | `2000` | 最大 token 数 |

### 相机服务配置

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `CAMERA_SERVICE_HOST` | `0.0.0.0` | TCP 服务监听地址 |
| `CAMERA_SERVICE_PORT` | `8888` | TCP 服务端口 |
| `CAMERA_COUNT` | `9` | 相机数量 |
| `CAMERA_IMAGE_DIR` | `camera_images` | 相机图片根目录 |
| `CAMERA_CONTROL_HOST` | `127.0.0.1` | 相机控制地址 |
| `CAMERA_CONTROL_PORT_BASE` | `9000` | 相机端口基址（相机N端口为 9000+N） |
| `CAMERA_CAPTURE_COMMAND` | `CAPTURE` | 拍照指令 |
| `CAMERA_CAPTURE_TIMEOUT` | `10.0` | 拍照超时（秒） |
| `CAMERA_WAIT_FOR_FILE` | `true` | 是否等待新文件 |
| `CAMERA_FILE_WAIT_TIMEOUT` | `15.0` | 文件等待超时（秒） |
| `CAMERA_FILE_CHECK_INTERVAL` | `0.5` | 文件检查间隔（秒） |
| `TRIGGER_COMMAND_PREFIX` | `XXXX` | 触发指令前缀 |

### 图像处理配置

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `IMAGE_RESIZE_ENABLED` | `true` | 是否启用图像缩放 |
| `IMAGE_MAX_SIZE` | `500` | 图像最长边像素数 |

---

## 目录结构

```
ocr-new/
├── config.py              # 配置文件
├── camera_service.py      # 相机 TCP 服务
├── instrument_reader.py   # 仪器读取器
├── read_instrument.py     # 命令行工具
├── visualizer.py          # 可视化工具
├── requirements.txt       # 依赖列表
├── demo/                  # 示例图片
├── camera_images/         # 相机图片目录
│   ├── camera_0/          # 相机0 图片
│   ├── camera_1/          # 相机1 图片
│   └── ...
└── output/                # 输出目录
```

---

## 支持的仪器类型

17类常见仪器：
- 电子天平、pH计、温度控制器
- 蠕动泵、离心机、水质检测仪
- 数字万用表、温度计、湿度计
- 压力表、电导率仪、溶解氧仪、浊度仪
- 表面张力仪、粘度计、气体检测仪
- 臭氧混调器、扭矩搅拌器

详见 [DEMO_INSTRUMENTS.md](DEMO_INSTRUMENTS.md)

---

## 相关文档

- [Demo 图片说明](DEMO_INSTRUMENTS.md)
