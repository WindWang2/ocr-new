# OCR 仪表读数识别系统

基于计算机视觉的仪表读数自动识别系统，支持多种仪表类型的自动识别和读数。

## 功能特性

- 支持多种仪表类型识别
- 自动拍照获取图像
- 仪表读数 OCR 识别
- 可视化标注结果

## 项目结构

```
├── camera_service.py     # 相机服务
├── config.py             # 配置文件
├── instrument_reader.py  # 仪表识别核心
├── read_instrument.py    # 读数入口
├── visualizer.py         # 可视化工具
├── requirements.txt      # 依赖
└── docs/                 # 文档
```

## 使用方法

```bash
pip install -r requirements.txt
python read_instrument.py
```

## 待开发

- 前端拍照界面
- API 服务化
- 移动端适配
