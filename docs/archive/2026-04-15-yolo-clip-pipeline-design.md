# YOLO + CLIP 多仪器识别流水线 设计文档

**日期**: 2026-04-15
**状态**: Draft → Approved
**作者**: Kevin + mobile-agent

## 背景

当前系统假设 **一个相机固定对应一台仪器**，通过硬编码映射 (F0→混调器, F1→天枰1号...) 直接送 LLM 读数。

新需求：
- 一个相机画面内可能同时出现 **多台仪器**
- 仪器位置不固定，可能移动、顺序不确定
- 需要实时流水线 (<2s 延迟)

## 方案选择

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| A: YOLO + CLIP | 轻量快速，CPU 可跑 | 需参考图库 | ✅ 采用 |
| B: YOLO + LLM | 无需参考图 | 慢 (>5s) | ❌ |
| 混合 | 最稳健 | 复杂度高 | 后续考虑 |

## 架构设计

### 三步流水线

```
┌───────────┐     ┌──────────────┐     ┌─────────────┐
│  Step 1   │     │    Step 2    │     │   Step 3    │
│  YOLO     │────▶│    CLIP      │────▶│   LLM       │
│  目标检测  │     │  仪器匹配    │     │  读数识别    │
└───────────┘     └──────────────┘     └─────────────┘
   原始图片         裁剪 + 对比          按类型读数
   ↓                ↓                    ↓
   N 个 bbox        仪器类型 + 置信度     结构化 JSON
```

### Step 1: YOLO 目标检测

- **模型**: YOLOv8n 或 YOLO11n (ultralytics)
- **任务**: 检测画面中的仪器区域，输出 bbox
- **类别**: 单类别 "instrument" (不需要区分仪器类型)
- **训练**: 用现有相机图片标注仪器框即可
- **推理**: `model.predict(image, conf=0.5)`
- **输出**: List[BBox] — 每个bbox = [x1, y1, x2, y2, confidence]

### Step 2: CLIP 仪器匹配

- **模型**: OpenAI CLIP ViT-B/32 (openai/clip)
- **流程**:
  1. 裁剪每个 bbox 区域
  2. 用 CLIP Image Encoder 提取裁剪图嵌入
  3. 与参考图库的嵌入计算余弦相似度
  4. 取最高相似度的仪器类型 (阈值 > 0.7，否则标记 unknown)
- **参考图库**: 暂复用现有 `templates.example_images` 字段
- **优化**: 参考图嵌入预计算并缓存，运行时只计算裁剪图嵌入

### Step 3: LLM 读数

- 复用现有 `MultimodalModelReader.read_instrument()`
- 对每个检测到的仪器，根据 Step 2 确定的类型，使用对应的 prompt 读数
- 支持并行处理多个仪器

## 数据模型变更

### 新增: 参考图嵌入缓存

```python
# instrument_embeddings.json — 预计算缓存
{
  "electronic_balance": {
    "embeddings": [[0.1, 0.2, ...], ...],  # 多张参考图的嵌入
    "image_paths": ["path/to/ref1.jpg", ...]
  },
  ...
}
```

### 数据库模板扩展

现有 `example_images` 字段暂作 CLIP 参考图使用，后续可能新建独立参考图管理。

## API 变更

### 新增端点: `POST /api/read-multi`

```json
// Request
{
  "camera_id": 1,
  "image_path": "optional custom path"
}

// Response
{
  "success": true,
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "instrument_type": "electronic_balance",
      "instrument_name": "电子天枰",
      "clip_confidence": 0.92,
      "readings": {"weight": 12.34},
      "read_confidence": 0.9
    },
    {
      "bbox": [x1, y1, x2, y2],
      "instrument_type": "ph_meter",
      "instrument_name": "PH仪",
      "clip_confidence": 0.88,
      "readings": {"ph_value": 7.2, "temperature": 25.3},
      "read_confidence": 0.85
    }
  ]
}
```

### 兼容性

- `POST /api/read` 保持不变，内部可走新流水线
- 相机配置表新增 `mode` 字段: "single" (旧模式) / "multi" (新模式)

## 新增文件结构

```
ocr-new/
├── backend/
│   ├── services/
│   │   ├── yolo_detector.py      # YOLO 目标检测服务
│   │   ├── clip_matcher.py       # CLIP 仪器匹配服务
│   │   └── pipeline.py           # 三步流水线编排
│   └── api/
│       └── main.py               # 新增 /api/read-multi 端点
├── reference_images/             # CLIP 参考图库 (暂复用 example_images)
├── models/                       # YOLO/CLIP 模型文件
│   ├── yolo_instrument.pt        # 训练后的 YOLO 权重
│   └── clip_cache.json           # 预计算嵌入缓存
└── docs/plans/
    └── 2026-04-15-yolo-clip-pipeline-design.md
```

## 依赖新增

```
ultralytics>=8.0    # YOLO
clip (openai-clip)  # 或 torch + transformers 加 CLIP
```

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| YOLO 训练数据不足 | 检测精度低 | 先用预训练 COCO 模型 + 迁移学习，逐步标注 |
| CLIP 参考图不够有代表性 | 匹配错误 | 设置低置信度阈值时 fallback 到 LLM |
| 无 GPU 时推理慢 | 超时 | YOLOn + CLIP ViT-B/32 CPU 可跑 <2s |
| 多仪器重叠遮挡 | 漏检 | YOLO 本身有一定重叠处理能力 |

## 实现优先级

1. **P0**: YOLO 检测 + bbox 裁剪 (核心)
2. **P0**: CLIP 匹配服务 (核心)
3. **P0**: 三步流水线编排 (核心)
4. **P1**: API 端点 + 前端适配
5. **P2**: 参考图管理 UI
6. **P2**: 嵌入缓存优化
7. **P3**: YOLO fine-tuning 工具链
