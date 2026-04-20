"""
方案B：SigLIP2图片嵌入匹配识别仪器类型 → 模型读数
流程：参考图生成向量库 → 新图生成向量 → 余弦相似度匹配 → 读数

用法:
  # 构建向量库
  python test_clip_identify.py build

  # 识别 + 读数
  python test_clip_identify.py run <读数模型> <图片路径> [图片路径 ...]

示例:
  python test_clip_identify.py build
  python test_clip_identify.py run 2b-new demo/1.jpg demo/1-2.jpg

环境变量: LMSTUDIO_BASE_URL=http://192.168.31.127:1234
模型路径: SIGLIP_MODEL_PATH（默认 /mnt/c/Users/wangj.KEVIN/Downloads/google/siglip2-base-patch16-224）
"""

import sys
import json
import os
import numpy as np
from pathlib import Path
from PIL import Image

LIBRARY_FILE = "clip_library.json"
SIGLIP_MODEL_PATH = os.environ.get(
    "SIGLIP_MODEL_PATH",
    "/mnt/c/Users/wangj.KEVIN/Downloads/google/siglip2-base-patch16-224"
)

# 参考图库：每种仪器类型 → 参考图列表（支持多张取平均）
REFERENCE_IMAGES = {
    "wuying_mixer_auto":     ["demo/1-1.jpg"],
    "wuying_mixer_manual":   ["demo/1-2.jpg"],
    "electronic_balance":    ["demo/2.jpg", "demo/3.jpg"],
    "ph_meter":              ["demo/4.jpg"],
    "water_quality_meter":   ["demo/5-1.jpg", "demo/5-2.jpg", "demo/5-3.jpg"],
    "surface_tension_meter": ["demo/6.jpg", "demo/6-1.jpg"],
    "torque_stirrer":        ["demo/7.jpg"],
    "temperature_controller":["demo/8.jpg"],
    "viscometer_6speed":     ["test_img/8.jpg"],
}

_model = None
_processor = None

def load_siglip():
    """懒加载 SigLIP2 模型"""
    global _model, _processor
    if _model is not None:
        return _model, _processor
    import torch
    from transformers import AutoModel, AutoProcessor
    print(f"加载 SigLIP2 模型: {SIGLIP_MODEL_PATH}")
    _model = AutoModel.from_pretrained(SIGLIP_MODEL_PATH).eval()
    _processor = AutoProcessor.from_pretrained(SIGLIP_MODEL_PATH)
    print(f"模型加载完成")
    return _model, _processor


def get_image_embedding(image_path: str) -> np.ndarray:
    """生成图片的 SigLIP2 嵌入向量"""
    import torch
    model, processor = load_siglip()
    img = Image.open(image_path).convert("RGB")
    inputs = processor(images=[img], return_tensors="pt")
    with torch.no_grad():
        out = model.get_image_features(**inputs)
    # transformers>=5.x returns an object; older versions return a tensor directly
    emb = out.pooler_output if hasattr(out, "pooler_output") else out
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy()[0]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_library():
    """为每种仪器类型生成参考向量（多张取平均），保存到库文件"""
    print(f"构建向量库 → {LIBRARY_FILE}")
    library = {}

    for instrument_type, image_paths in REFERENCE_IMAGES.items():
        print(f"  {instrument_type}: ", end="", flush=True)
        embeddings = []
        for img_path in image_paths:
            if not Path(img_path).exists():
                print(f"[跳过 {img_path}]", end=" ")
                continue
            emb = get_image_embedding(img_path)
            embeddings.append(emb)
            print(f"✓", end=" ", flush=True)

        if embeddings:
            avg_emb = np.mean(embeddings, axis=0)
            avg_emb = avg_emb / np.linalg.norm(avg_emb)  # 归一化
            library[instrument_type] = avg_emb.tolist()
            print(f"→ dim={len(avg_emb)}")
        else:
            print("无可用图片，跳过")

    with open(LIBRARY_FILE, "w") as f:
        json.dump(library, f)
    print(f"\n向量库已保存：{len(library)} 种仪器")


def load_library() -> dict:
    """加载向量库"""
    if not Path(LIBRARY_FILE).exists():
        print(f"向量库不存在，请先运行: python {sys.argv[0]} build")
        sys.exit(1)
    with open(LIBRARY_FILE) as f:
        raw = json.load(f)
    return {k: np.array(v, dtype=np.float32) for k, v in raw.items()}


def identify_by_clip(image_path: str, library: dict) -> tuple[str, float]:
    """用 SigLIP2 嵌入匹配识别仪器类型，返回 (类型, 相似度)"""
    emb = get_image_embedding(image_path)

    best_type, best_score = "unknown", -1.0
    scores = {}
    for instrument_type, ref_emb in library.items():
        score = cosine_similarity(emb, ref_emb)
        scores[instrument_type] = score
        if score > best_score:
            best_score = score
            best_type = instrument_type

    # 打印所有分数（调试用）
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for t, s in sorted_scores[:4]:
        marker = " ←" if t == best_type else ""
        print(f"    {s:.4f}  {t}{marker}")

    return best_type, best_score


def get_unit(instrument_type: str, field: str) -> str:
    from instrument_reader import DynamicInstrumentLibrary
    template = DynamicInstrumentLibrary.get_template(instrument_type)
    if template:
        for f in template.get("fields", []):
            if f.get("name") == field:
                return f.get("unit", "")
    return ""


def run(read_model: str, images: list):
    """识别 + 读数"""
    import logging
    logging.basicConfig(level=logging.WARNING)

    library = load_library()
    print(f"向量库已加载：{len(library)} 种仪器\n")

    from instrument_reader import MultimodalModelReader, DynamicInstrumentLibrary
    reader = MultimodalModelReader(model_name=read_model)

    for img_path in images:
        if not Path(img_path).exists():
            print(f"[跳过] 文件不存在: {img_path}")
            continue

        print(f"\n{'='*50}")
        print(f"图片: {img_path}")
        print(f"{'='*50}")

        # 步骤1：SigLIP2 嵌入匹配
        print("[步骤1] SigLIP2嵌入匹配...")
        instrument_type, score = identify_by_clip(img_path, library)
        template = DynamicInstrumentLibrary.get_template(instrument_type)
        instrument_name = template.get("name", instrument_type) if template else instrument_type
        print(f"  → {instrument_type} ({instrument_name})  相似度={score:.4f}")

        # 步骤2：模型读数
        print(f"[步骤2] 读取数值 ({read_model})...")
        read_result = reader.read_instrument(img_path, instrument_type)

        if "error" in read_result:
            print(f"  失败: {read_result['error']}")
            continue

        print(f"  读数 (带单位):")
        for k, v in read_result.items():
            if v is not None:
                unit = get_unit(instrument_type, k)
                unit_str = f" {unit}" if unit else ""
                print(f"    {k}: {v}{unit_str}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "build":
        build_library()
    elif cmd == "run":
        if len(sys.argv) < 4:
            print("用法: python test_clip_identify.py run <读数模型> <图片路径> ...")
            sys.exit(1)
        run(sys.argv[2], sys.argv[3:])
    else:
        print(__doc__)
