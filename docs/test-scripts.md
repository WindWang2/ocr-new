# 测试脚本说明

项目包含以下测试和验证脚本，均在项目根目录下运行。建议在 `dfine` Conda 环境中执行。

---

## 1. `read_instrument.py` — [核心] 集成推理测试

这是目前最主要的测试脚本，模拟了完整的“检测-裁剪-精读”流程。它使用 YOLO26x 定位仪器，并自动调用本地 LLM 进行读数。

```bash
# 测试单张图片 (自动检测、裁剪并识别图中所有仪器)
python read_instrument.py demo/1.jpg

# 测试目录下所有图片
python read_instrument.py demo/
```

**输出：**
- 控制台输出识别到的仪器类别（F0-F8）、坐标、置信度以及具体的 JSON 读数。
- `output/` 目录下会生成标注了检测框的图片。

---

## 2. `test_camera.py` — 相机 TCP 连接测试

逐台测试相机控制端口的 TCP 连通性，发送拍照指令并接收响应。

```bash
# 测试所有相机 F0-F8
python test_camera.py
```

---

## 3. `test_read.py` — OCR 读数专项测试 (旧版逻辑)

对指定图片执行 OCR 识别。注意：此脚本主要走旧的“全图识别”逻辑，不带 YOLO 裁剪。

```bash
# 用 2B 模型测试单张图片
python test_read.py 2b demo/5-1.jpg
```

---

## 4. `tests/` 目录 — 单元测试与集成测试

使用 `pytest` 运行标准测试套件。

```bash
# 运行全量测试
python -m pytest tests/ -v

# 只测试 YOLO 检测器
python -m pytest tests/test_yolo_detector.py -v
```

---

## 5. `visualizer.py` — 结果可视化工具

用于快速查看 YOLO 检测结果并验证 NMS 效果。

```bash
# 可视化检测框
python visualizer.py --image demo/1.jpg
```

---

## 目录说明

- `demo/`：存放用于快速测试的 JPG 样例图。
- `camera_images/`：存放真实/模拟相机拍摄的原始图片及自动生成的 `crops/` 裁剪图。
- `output/`：存放测试脚本生成的标注结果图。
