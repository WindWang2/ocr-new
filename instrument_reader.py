"""
仪器读数识别系统
核心逻辑：YOLO26x 目标检测与分类 -> 自动裁剪特写 -> 多模态 LLM 读数
后端支持：Llama.cpp (OpenAI 兼容 API)
"""

import os
import base64
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union, Type
from PIL import Image
from config import Config

from pydantic import create_model, Field

logger = logging.getLogger(__name__)


from backend.models.database import get_all_templates, get_template

def get_pydantic_model_for_instrument(instrument_type: str):
    """根据仪器模板字段，动态创建 Pydantic 模型。"""
    t = DynamicInstrumentLibrary.get_template(instrument_type)
    if not t:
        return None
    fields_config = t.get('fields', [])
    model_fields = {}
    for f in fields_config:
        # 绝大多数读数是 float，默认设为 Optional[float]
        # 注意：这里我们强制设为 Optional 以容忍部分读取失败
        model_fields[f['name']] = (Optional[float], Field(default=None, description=f.get('label', '')))
    
    DynamicModel = create_model(f'{instrument_type}Model', **model_fields)
    return DynamicModel

from backend.instrument_configs import INSTRUMENT_CONFIGS

class DynamicInstrumentLibrary:
    """动态仪器配置库：以中央配置文件为准，支持数据库动态覆盖"""

    @classmethod
    def get_route_map(cls) -> Dict[int, int]:
        """获取仪器到物理相机的路由映射"""
        # 1. 默认从配置文件加载
        route_map = {cfg["yolo_cls_id"]: cfg["camera_id"] for cfg in INSTRUMENT_CONFIGS.values()}
        
        # 2. 尝试从数据库覆盖 (用户在前端修改的结果)
        try:
            from backend.models.database import get_config
            saved = get_config("instrument_camera_mapping", default=None)
            if saved:
                for k, v in saved.items():
                    route_map[int(k)] = int(v)
        except Exception as e:
            logger.warning(f"无法加载动态路由覆盖: {e}")
            
        return route_map

    @classmethod
    def get_physical_camera_id(cls, instrument_id: int) -> int:
        """根据仪器 ID 获取对应的物理相机 ID"""
        route = cls.get_route_map()
        return route.get(instrument_id, instrument_id)

    @classmethod
    def get_template(cls, instrument_key: str) -> Optional[Dict[str, Any]]:
        """获取仪器的识别模板（优先从数据库获取，否则回退到配置文件）"""
        # 1. 尝试作为 ID (0-8) 从数据库获取
        inst_type_id = str(instrument_key).replace('F', '').replace('f', '')
        try:
            from backend.models.database import get_template
            t = get_template(inst_type_id)
            if t:
                # 转换数据库中的 JSON 字符串
                if isinstance(t, dict):
                    t['fields'] = json.loads(t.get('fields_json', '[]'))
                    t['keywords'] = json.loads(t.get('keywords_json', '[]'))
                    t['example_images'] = json.loads(t.get('example_images_json') or '[]')
                    return t
        except Exception as e:
            logger.warning(f"从数据库获取模板失败: {e}")

        # 2. 回退到 INSTRUMENT_CONFIGS 静态配置
        f_key = f"F{inst_type_id}"
        config = INSTRUMENT_CONFIGS.get(f_key)
        if config:
            # 转换为统一的字典格式供下游使用
            return {
                'instrument_type': f_key,
                'name': config.get('name'),
                'prompt_template': config.get('prompt'),
                'fields': [], # 静态配置暂无详细字段定义
                'post_process': config.get('post_process')
            }
        return None

    @classmethod
    def get_camera_prompt(cls, camera_name_or_id: str) -> str:
        """根据相机代号（如 F3）或仪器 ID 获取对应的 Prompt"""
        t = cls.get_template(camera_name_or_id)
        if t:
            return t.get('prompt_template', "")
        return ""

    @classmethod
    def get_instrument_prompt(cls, instrument_type: str) -> str:
        """获取仪器类型的 Prompt"""
        return cls.get_camera_prompt(instrument_type)
    # Legacy hardcoded templates removed - using database driven lookup in get_camera_prompt

    @classmethod
    def get_instrument_type_from_camera(cls, camera_name: str, parsed: dict = None) -> str:
        """从相机代号获取仪器显示名称（动态从数据库获取）"""
        try:
            inst_type_id = str(camera_name).replace('F', '').replace('f', '')
            from backend.models.database import get_template
            t = get_template(inst_type_id)
            if t:
                # 如果是混料器，根据模式返回更详细的显示名
                if inst_type_id == "0" and parsed:
                    mode = parsed.get("mode", "auto")
                    return f"{t['name']}({mode})"
                return t['name']
        except Exception:
            pass
        return "未知仪器"

    @classmethod
    def get_post_process_type(cls, instrument_id: int) -> Optional[str]:
        """获取仪器的后处理逻辑类型"""
        t = cls.get_template(str(instrument_id))
        if t:
            return t.get('post_process')
        return None

    @classmethod
    def get_all(cls):
        """获取所有仪器模板（用于识别）"""
        try:
            from backend.models.database import get_all_templates
            templates = get_all_templates()
            for t in templates:
                if isinstance(t, dict):
                    t['fields'] = json.loads(t.get('fields_json', '[]'))
                    t['keywords'] = json.loads(t.get('keywords_json', '[]'))
                    t['example_images'] = json.loads(t.get('example_images_json') or '[]')
            return templates
        except Exception as e:
            logger.warning(f"获取所有模板失败: {e}")
            return []

    @classmethod
    def identify_instrument_prompt(cls) -> str:
        """获取仪器类型识别的prompt（从数据库动态生成）"""
        templates = cls.get_all()
        
        rules_text = ""
        for i, t in enumerate(templates, 1):
            keywords_str = "、".join([f'"{kw}"' for kw in t["keywords"]])
            rules_text += f"{i}. {t['instrument_type']}: {t['description']} (识别关键词: {keywords_str})\n"
            
        instrument_types = ", ".join([t['instrument_type'] for t in templates])

        prompt = f"""识别图片中的仪器类型，按以下优先顺序判断：

{rules_text}

【重要】你必须严格按照以下JSON格式输出，不要输出任何其他内容（不要分析、不要解释、不要思考过程）：

{{"instrument_type": "选中的仪器类型标识", "confidence": 0.95}}

输出要求：
1. 只输出一行JSON，不要有其他任何文字
2. 不要使用Markdown代码块
3. 不要输出分析过程
4. instrument_type 必须是以下选项之一: {instrument_types}

"""
        return prompt


class MultimodalModelReader:
    """多模态大模型读取器（Llama.cpp 后端）"""

    def __init__(self, model_name: str = None, base_url: str = None, provider=None):
        """
        初始化模型
        Args:
            model_name: 模型名称，默认从配置读取
            base_url: API地址，默认从配置读取
            provider: LLM Provider 实例（可选，传入时忽略 model_name/base_url）
        """
        if provider is not None:
            self._provider = provider
            self.model_name = provider.model_name
            self.base_url = ""
        else:
            from backend.services.llm_provider import create_provider, LLMConfig
            
            self.provider_type = Config.DEFAULT_LLM_PROVIDER
            self.model_name = model_name or Config.LMSTUDIO_MODEL
            
            if self.provider_type == "local_vlm":
                self.base_url = Config.LOCAL_VLM_PATH
            else:
                self.base_url = base_url or Config.LMSTUDIO_BASE_URL

            self._provider = create_provider(LLMConfig(
                provider=self.provider_type,
                model_name=self.model_name,
                base_url=self.base_url,
            ))

        logger.info("使用 LLM 后端, 模型: %s", self.model_name)

    def analyze_image(self, image_source: Union[str, Image.Image], prompt: str, call_type: str = "unknown", instrument_type: str = None) -> Dict[str, Any]:
        """Analyze image using Multimodal LLM"""
        print(f"\n!!!!!!!! [OCR_DEBUG] analyze_image CALLED: call_type={call_type}, instrument={instrument_type} !!!!!!!!\n")
        try:
            # 读取图片，统一转为 RGB JPEG 发送（兼容灰度图、BMP 等格式）
            from PIL import Image
            import io
            import os
            
            if isinstance(image_source, str):
                try:
                    img = Image.open(image_source).convert("RGB")
                except Exception as e:
                    return {"error": f"LLM_OPEN_ERR [{os.path.abspath(image_source)}]: {e}"}
                image_path_str = image_source
            else:
                img = image_source.convert("RGB")
                image_path_str = "memory_image"
            
            # 统一执行缩放逻辑：送入 LLM 的图片最长边不超过 500 像素
            if Config.IMAGE_RESIZE_ENABLED:
                w, h = img.size
                max_dim = max(w, h)
                if max_dim > Config.IMAGE_MAX_SIZE:
                    scale = Config.IMAGE_MAX_SIZE / max_dim
                    new_w, new_h = int(w * scale), int(h * scale)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    logger.info(f"LLM 输入图已强制缩放: {w}x{h} -> {new_w}x{new_h}")
                
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            base64_images = [base64.b64encode(buf.getvalue()).decode('utf-8')]

            # 若提供了仪器类型，尝试加载示例图片（Few-shot）
            if instrument_type:
                template = DynamicInstrumentLibrary.get_template(instrument_type)
                if template and template.get('example_images'):
                    for ex_path in template['example_images']:
                        try:
                            if os.path.exists(ex_path):
                                ex_img = Image.open(ex_path).convert("RGB")
                                ex_buf = io.BytesIO()
                                ex_img.save(ex_buf, format="JPEG", quality=95)
                                base64_images.append(base64.b64encode(ex_buf.getvalue()).decode('utf-8'))
                            else:
                                logger.warning(f"Example image not found: {ex_path}")
                        except Exception as e:
                            logger.warning(f"Failed to load example image {ex_path}: {e}")

            # 构建消息列表：系统提示词 + 用户提示词
            # 系统提示词强制模型仅输出 JSON
            system_prompt = (
                "You are a professional industrial instrument reading assistant. "
                "You MUST output raw JSON only. Do not provide any analysis, explanation, or conversational filler. "
                "Strictly follow the JSON schema provided in the user prompt."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            # 调用 LLM Provider
            result_text = self._provider.chat(
                messages=messages,
                images=base64_images,
                temperature=Config.MODEL_TEMPERATURE,
                max_tokens=Config.MODEL_MAX_TOKENS,
            )
            
            # 强化调试日志：清理掉那些烦人的 <|image|>
            clean_log = re.sub(r'<\|image\|>', '', result_text).strip()
            print(f"\n[DEBUG RAW LLM] (Cleaned) >>>\n{clean_log}\n<<< [DEBUG RAW LLM]\n")
            
            parsed = self._parse_json_response(result_text)
            
            # 【核心修正】不再使用 Pydantic 进行严格过滤，仅在结果缺失时填充 null
            if instrument_type and "error" not in parsed:
                template = DynamicInstrumentLibrary.get_template(instrument_type)
                if template:
                    for field in template.get('fields', []):
                        f_name = field['name']
                        if f_name not in parsed:
                            parsed[f_name] = None
                        # 不再强制转为 float，保留原始字符串供后处理引擎检查格式（如小数点缺失）
            
            if "error" in parsed:
                logger.warning("分析失败或解析错误，原始响应: %s", clean_log)

            # 保存响应到JSON文件（调试用）
            self._save_response_debug(image_path_str, call_type, prompt, result_text, parsed)

            return parsed
        except Exception as e:
            logger.error("多模态模型分析失败: %s", e)
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
        except Exception as e:
            logger.error("多模态模型分析失败: %s", e)
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _validate_with_pydantic(self, parsed_json: dict, instrument_type: str) -> dict:
        """使用动态创建的 Pydantic 模型验证 LLM 响应结果"""
        model_class = get_pydantic_model_for_instrument(instrument_type)
        if not model_class:
            return parsed_json
        try:
            # 兼容 Pydantic V2
            validated = model_class(**parsed_json)
            return validated.model_dump()
        except Exception as e:
            logger.warning(f"Validation failed for {instrument_type}: {e}")
            # 返回校验错误信息，并保留原始解析数据供排查
            return {"error": f"Validation failed: {str(e)}", "raw_parsed": parsed_json}

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON response, supporting nested JSON and Markdown code blocks"""
        # Clean text
        text = text.strip()

        # Remove ellipses
        text = re.sub(r',\s*\.\.\.\s*', '', text)
        text = re.sub(r'\.\.\.', '', text)
        
        # Auto-fix common LLM JSON mistake: missing quotes on keys
        # E.g., {weight": "4033"} -> {"weight": "4033"}
        # Or {weight: 4033} -> {"weight": 4033}
        fixed_text = re.sub(r'([{,]\s*)["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?\s*:', r'\1"\2":', text)

        # Try to extract JSON from Markdown code blocks
        code_block_match = list(re.finditer(r'```(?:json)?\s*([\s\S]*?)```', fixed_text))
        if code_block_match:
            # 取最后一个代码块，因为前面的可能是 prompt 中的示例
            json_text = code_block_match[-1].group(1).strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass

        try:
            # 先尝试直接解析整个文本
            return json.loads(fixed_text)
        except (json.JSONDecodeError, ValueError):
            pass

        try:
            # 暴力提取所有可能的 JSON 块，选最后一个（最可能是模型真实的输出）
            # 找所有 {
            start_indices = [i for i, char in enumerate(fixed_text) if char == '{']
            valid_jsons = []
            
            for start in start_indices:
                depth = 0
                for i in range(start, len(fixed_text)):
                    if fixed_text[i] == '{':
                        depth += 1
                    elif fixed_text[i] == '}':
                        depth -= 1
                        if depth == 0:
                            json_str = fixed_text[start:i + 1]
                            try:
                                parsed = json.loads(json_str)
                                valid_jsons.append(parsed)
                            except json.JSONDecodeError:
                                pass
                            break # 找到当前 { 对应的闭合 } 后跳出内层循环
            
            if valid_jsons:
                return valid_jsons[-1] # 返回最后一个合法的 JSON
            
            # 【终极兜底】：如果连 { } 都坏了，直接用正则暴力提取数字（仅作为最后一招）
            logger.warning("未能在文本中找到合法的 JSON 对象，尝试正则降级提取: %s", text[:200])
            fallback_dict = {}
            # 找所有 键: 值
            matches = re.finditer(r'["\']?([a-zA-Z_][a-zA-Z0-9_]*)["\']?\s*:\s*["\']?([\d\.]+)["\']?', fixed_text)
            for m in matches:
                key, val = m.groups()
                try:
                    fallback_dict[key] = float(val)
                except ValueError: pass
            
            if fallback_dict:
                return fallback_dict

            return {"error": "未能在文本中找到合法的 JSON 对象", "raw_text": text}
        except Exception as e:
            logger.error("解析响应时发生异常: %s", e)
            return {"error": str(e), "raw_text": text}

    def _save_response_debug(self, image_path: str, call_type: str, prompt: str, raw_response: str, parsed: Dict):
        """保存大模型响应到JSON文件（调试用）"""
        from datetime import datetime

        try:
            # 创建json目录
            json_dir = Path("json")
            json_dir.mkdir(exist_ok=True)

            # 生成文件名：图片名_调用类型_时间戳.json
            image_name = Path(image_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{image_name}_{call_type}_{timestamp}.json"
            filepath = json_dir / filename

            # 构建保存数据
            data = {
                "timestamp": datetime.now().isoformat(),
                "image_path": str(image_path),
                "call_type": call_type,
                "model": self.model_name,
                "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                "raw_response": raw_response,
                "parsed_response": parsed
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("响应已保存到: %s", filepath)
        except Exception as e:
            logger.warning("保存调试JSON失败: %s", e)

    def identify_instrument(self, image_path: str) -> Dict[str, Any]:
        """识别仪器类型，对易混淆的类型做二次确认"""
        prompt = DynamicInstrumentLibrary.identify_instrument_prompt()
        result = self.analyze_image(image_path, prompt, call_type="identify")

        if "error" in result:
            return result

        # wuying_mixer_auto/manual 容易混淆，再跑一次取多数票
        instrument_type = result.get("instrument_type", "")
        if instrument_type in ("wuying_mixer_auto", "wuying_mixer_manual"):
            result2 = self.analyze_image(image_path, prompt, call_type="identify")
            type2 = result2.get("instrument_type", "")
            if type2 != instrument_type and type2 in ("wuying_mixer_auto", "wuying_mixer_manual"):
                # 两次结果不一致，再跑第三次决定
                result3 = self.analyze_image(image_path, prompt, call_type="identify")
                type3 = result3.get("instrument_type", "")
                # 三次取多数
                votes = [instrument_type, type2, type3]
                final_type = max(set(votes), key=votes.count)
                if final_type != instrument_type:
                    logger.info("identify 多数票修正: %s → %s (votes: %s)", instrument_type, final_type, votes)
                    result["instrument_type"] = final_type

        return result

    def read_instrument(self, image_path: str, instrument_type: str, ocr_text: str = None) -> Dict[str, Any]:
        """读取仪器数值"""
        prompt = DynamicInstrumentLibrary.get_instrument_prompt(instrument_type)
        if ocr_text:
            prompt = f"【OCR识别文字参考】\n{ocr_text}\n\n{prompt}"
        return self.analyze_image(image_path, prompt, call_type="read", instrument_type=instrument_type)


class InstrumentReader:
    """仪器读数主类 - 仅使用多模态模型"""

    def __init__(self, model_name: str = None, provider=None):
        """
        初始化仪器读数系统
        Args:
            model_name: 多模态模型名称，默认从配置读取
            provider: LLM Provider 实例（可选）
        """
        logger.info("初始化仪器读数系统...")
        if provider is not None:
            logger.info("后端: %s", provider.provider_type)
            logger.info("模型: %s", provider.model_name)
            self.mm_reader = MultimodalModelReader(provider=provider)
        else:
            self.mm_reader = MultimodalModelReader(model_name=model_name)
            logger.info("后端: %s", self.mm_reader.provider_type)
            logger.info("模型: %s", self.mm_reader.model_name)

        logger.info("系统初始化完成！")

    @staticmethod
    def _extract_camera_name(image_path: str) -> Optional[str]:
        """
        从图片路径或文件名中提取相机名称（F0-F8）。
        支持路径格式：
          - .../F0/20260314/xxx.jpg
          - .../xxx_F0-I0_OK.jpg
          - .../camera_0/xxx.jpg  → F0
        """
        path_str = str(image_path)

        # 从文件名提取：xxx_F0-I0_OK.jpg
        fname_match = re.search(r'_([Ff]\d)-[Ii]\d', path_str)
        if fname_match:
            return fname_match.group(1).upper()

        # 从目录名提取：.../F0/...
        dir_match = re.search(r'[\\/]([Ff]\d)[\\/]', path_str)
        if dir_match:
            return dir_match.group(1).upper()

        # 从 camera_N 目录提取：.../camera_0/...
        cam_num_match = re.search(r'camera[_\-](\d)', path_str, re.IGNORECASE)
        if cam_num_match:
            return f"F{cam_num_match.group(1)}"

        return None

    def detect_only(self, image_path: str) -> Dict[str, Any]:
        """仅运行检测并返回裁剪图路径，不进行读取"""
        print(f"\n[DEBUG_DETECT] Entering detect_only: {image_path}\n")
        from PIL import Image
        from pathlib import Path

        # 核心逻辑：防止对已经是裁剪图的图片进行二次裁剪
        path_obj = Path(image_path)
        if "crops" in path_obj.parts or "_crop_" in path_obj.name:
            logger.info("输入图片已是裁剪图，跳过二次裁剪逻辑")
            # 尝试计算相对于挂载根目录的路径
            try:
                parts = list(path_obj.parts)
                start_idx = 0
                for i in range(len(parts)-1, -1, -1):
                    if re.match(r'^[Ff]\d+$', parts[i]):
                        start_idx = i
                        break
                rel_path = "/".join(parts[start_idx:])
            except:
                rel_path = path_obj.name
                
            return {"success": True, "results": [{
                "success": True,
                "bbox": [0,0,0,0],
                "yolo_confidence": 1.0,
                "class_id": int(re.search(r'F(\d+)', path_obj.name).group(1)) if "F" in path_obj.name else 0,
                "cropped_image_path": rel_path.replace("\\", "/"),
                "image_source": image_path
            }]}

        # 懒加载 YOLO
        if not hasattr(self, 'yolo_detector'):
            print("[DEBUG_DETECT] Initializing YOLO...")
            from backend.services.yolo_detector import YOLOInstrumentDetector
            self.yolo_detector = YOLOInstrumentDetector(confidence_threshold=0.1, iou_threshold=0.15)
            
        try:
            img = Image.open(image_path)
        except Exception as e:
            return {"success": False, "error": f"YOLO_IMAGE_OPEN_ERR [{image_path}]: {e}"}

        detections = self.yolo_detector.detect(img)
        print(f"\n[DEBUG_DETECT] YOLO found {len(detections)} targets\n")
        if not detections:
            logger.info("YOLO 未检测到任何目标")
            return {"success": False, "error": "未检出结果"}

        logger.info("YOLO 检测到 %d 个目标", len(detections))

        all_results = []
        for det in detections:
            x1, y1, x2, y2, yolo_conf, class_id = det
            detected_camera_name = f"F{int(class_id)}"
            
            # Crop image (from original high-res img)
            cropped_img_high_res = self.yolo_detector.crop_instrument(img, det, padding=15)
            
            # Save high-res cropped image first
            orig_path = Path(image_path)
            crops_dir = orig_path.parent / "crops"
            crops_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = __import__("time").strftime("%H%M%S")
            # 统一使用 .png 保持高清无损
            crop_filename = f"{orig_path.stem}_crop_{detected_camera_name}_{timestamp}.png"
            crop_path = crops_dir / crop_filename
            cropped_img_high_res.save(crop_path, "PNG", optimize=False)
            
            # 计算相对于挂载根目录的干净路径
            try:
                parts = list(crop_path.parts)
                start_idx = 0
                for i in range(len(parts)-1, -1, -1):
                    if re.match(r'^[Ff]\d+$', parts[i]):
                        start_idx = i
                        break
                relative_crop_path = "/".join(parts[start_idx:])
            except:
                relative_crop_path = f"{detected_camera_name}/crops/{crop_filename}"
                
            all_results.append({
                "success": True,
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "yolo_confidence": float(yolo_conf),
                "class_id": int(class_id),
                "cropped_image_path": str(relative_crop_path).replace("\\", "/"),
                "image_source": crop_path 
            })
            
        return {"success": True, "results": all_results}
            
        return {"success": True, "results": all_results}

    def read_instrument(self, image_path: str, target_class_id: int = None) -> Dict[str, Any]:
        """识别仪表：先检测后读取"""
        print(f"\n[DEBUG_ENTRY] read_instrument CALLED: path={image_path}, target={target_class_id}\n")
        
        # 1. 动态调整检测阈值：如果指定了目标，临时降到 0.05 以捕获弱特征目标 (如 F7)
        original_conf = self.yolo_detector.confidence_threshold
        if target_class_id is not None:
            self.yolo_detector.confidence_threshold = 0.05
            
        detect_result = self.detect_only(image_path)
        self.yolo_detector.confidence_threshold = original_conf # 立即恢复原阈值
        
        # 2. 如果检测到了内容
        if detect_result.get("success") and detect_result.get("results"):
            all_detections = detect_result["results"]
            
            if target_class_id is not None:
                # 策略：只要用户指定了目标，就只在检出的框里找这个目标
                target_matches = [d for d in all_detections if d["class_id"] == target_class_id]
                
                if target_matches:
                    best_det = max(target_matches, key=lambda x: x["yolo_confidence"])
                    logger.info(f"YOLO 成功(通过降低阈值)捕获目标 F{target_class_id}，执行特写读取")
                    return self._read_with_det_info(image_path, best_det, target_class_id)
                else:
                    # 如果降了阈值也没抓到 F7，但抓到了别的，也应该忽略别的，退回 F7 的全图读取
                    logger.warning(f"调低阈值后仍未发现 F{target_class_id}，尝试对全图进行强行读取...")
                    return self._read_by_camera(image_path, f"F{target_class_id}")
            
            # 如果没有指定目标，则执行普通多目标读取
            all_results = []
            for det_info in all_detections:
                res = self._read_with_det_info(image_path, det_info)
                all_results.append(res)
                
            if len(all_results) == 1: return all_results[0]
            elif len(all_results) > 1:
                combined_readings = {}
                for r in all_results: combined_readings.update(r.get("readings", {}))
                return {
                    "success": True, "multiple_targets": True, "instrument_name": "Multiple Instruments",
                    "readings": combined_readings, "all_results": all_results, "method": "yolo_multi_crop"
                }

        # 3. 核心逻辑修正：如果 YOLO 完全没检测到，但用户指定了 target_class_id，强行读取
        if target_class_id is not None:
            logger.warning(f"YOLO 完全未能检测到目标，强行对全图执行 F{target_class_id} 识别")
            return self._read_by_camera(image_path, f"F{target_class_id}")
            
        logger.warning("未检测到任何仪器目标，退回旧版全图识别流程...")
        return self._read_by_identification(image_path)

    def _read_with_det_info(self, original_image_path: str, det_info: Dict, override_class_id: int = None) -> Dict:
        """封装：根据检测信息执行单次读取"""
        class_id = override_class_id if override_class_id is not None else det_info["class_id"]
        detected_camera_name = f"F{class_id}"
        cropped_img_path = det_info["image_source"]
        
        # 从中央配置获取 Prompt
        prompt = DynamicInstrumentLibrary.get_template(str(class_id))
        if prompt:
            print(f"[DEBUG_CROP] Analyzing crop for F{class_id}: {cropped_img_path}")
            result = self._read_by_camera(str(cropped_img_path), detected_camera_name)
        else:
            result = {"success": False, "error": f"未找到 F{class_id} 的配置"}
            
        # 合并检测信息
        result.update({
            "bbox": det_info["bbox"],
            "yolo_confidence": det_info["yolo_confidence"],
            "class_id": class_id, 
            "yolo_class_id": det_info["class_id"],
            "cropped_image_path": det_info["cropped_image_path"]
        })
        
        # 动态执行强大的后处理引擎 (如天平的小数点纠正、时间转换)
        from backend.services.post_processor import apply_post_processing
        if "readings" in result:
            result["readings"] = apply_post_processing(class_id, result["readings"])
            
        return result

    def _read_by_camera(self, image_source: Union[str, Image.Image], camera_name: str) -> Dict[str, Any]:
        """使用相机专用prompt直接读取（单步，跳过识别）"""
        logger.info("相机 %s: 使用专用prompt直接读取", camera_name)

        # 在单步读取中，尝试预先确定仪器类型以支持 Pydantic 校验
        mock_parsed = {"mode": "auto"} if camera_name == "F0" else {}
        instrument_type = DynamicInstrumentLibrary.get_instrument_type_from_camera(camera_name, mock_parsed)

        prompt = DynamicInstrumentLibrary.get_instrument_prompt(camera_name)
        parsed = self.mm_reader.analyze_image(image_source, prompt, call_type="read", instrument_type=instrument_type)

        if "error" in parsed:
            # 如果是 Pydantic 校验失败，尝试切换到 manual 模式再试一次 (针对 F0)
            if camera_name == "F0" and "Validation failed" in parsed.get("error", ""):
                logger.info("F0 auto模式校验失败，尝试以 manual 模式读取...")
                instrument_type = "wuying_mixer_manual"
                parsed = self.mm_reader.analyze_image(image_source, prompt, call_type="read", instrument_type=instrument_type)
            
            if "error" in parsed:
                return {"success": False, "error": f"数值读取失败: {parsed['error']}"}

        # 重新确定最终的仪器类型
        instrument_type = DynamicInstrumentLibrary.get_instrument_type_from_camera(camera_name, parsed)
        template = DynamicInstrumentLibrary.get_template(camera_name.replace('F', '').replace('f', ''))
        instrument_name = template['name'] if template else camera_name
        readings = parsed  # 平铺JSON直接作为readings
        class_id = int(camera_name.replace('F', '').replace('f', ''))

        # 动态执行强大的后处理引擎
        from backend.services.post_processor import apply_post_processing
        readings = apply_post_processing(class_id, readings)

        result = {
            "success": True,
            "instrument_type": instrument_type,
            "instrument_name": instrument_name,
            "camera_name": camera_name,
            "class_id": class_id,
            "type_confidence": 1.0,
            "readings": readings,
            "confidence": 0.9,
            "method": "camera_direct",
        }

        for attr, value in readings.items():
            if value is not None:
                logger.info("  %s: %s", attr, value)

        return result

    def _get_ocr_text(self, image_path: str) -> Optional[str]:
        """调用 OCR 模型提取图片文字"""
        # 如果使用的是本地 VLM，通常不需要单独的 OCR 步骤，或者 8080 服务本就不存在
        if Config.DEFAULT_LLM_PROVIDER == "local_vlm":
            logger.debug("使用 local_vlm，跳过 8080 OCR 步骤")
            return None

        try:
            import httpx
            from PIL import Image
            import io as _io
            import os
            # Ensure path is absolute
            if not os.path.isabs(image_path):
                base_dir = Path(__file__).parent
                potential_path = str(base_dir / "camera_images" / image_path)
                if os.path.exists(potential_path):
                    image_path = potential_path
                else:
                    fallback = str(base_dir / image_path.replace("camera_images/", ""))
                    if os.path.exists(fallback):
                        image_path = fallback
                        
            img = Image.open(image_path).convert("RGB")
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            
            logger.info("尝试调用 8080 OCR 服务...")
            r = httpx.post(
                f"{Config.LMSTUDIO_BASE_URL}/v1/chat/completions",
                json={
                    "model": Config.LMSTUDIO_OCR_MODEL,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": "识别图片中所有文字，原样输出，不要解释。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    ]}],
                    "max_tokens": 500,
                    "temperature": 0.0,
                },
                timeout=5, # 缩短超时时间，避免挂死
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("OCR提取失败（服务可能未启动）: %s", e)
            return None

    def _read_by_identification(self, image_path: str) -> Dict[str, Any]:
        """两步识别流程：OCR关键词识别（默认）→ 读数；失败则退回LLM识别"""
        # 步骤1: OCR提取文字 + 关键词识别
        logger.info("步骤1: OCR提取文字识别仪器类型...")
        ocr_text = self._get_ocr_text(image_path)
        instrument_type = "unknown"
        type_confidence = 0.0
        method = "multimodal"

        if ocr_text:
            instrument_type = DynamicInstrumentLibrary.identify_by_ocr_keywords(ocr_text)
            logger.info("OCR关键词识别: %s", instrument_type)

        if instrument_type == "unknown":
            # Fallback: LLM识别
            logger.info("OCR识别未匹配，退回LLM识别...")
            identification = self.mm_reader.identify_instrument(image_path)
            if "error" in identification:
                return {"success": False, "error": f"仪器类型识别失败: {identification['error']}"}
            instrument_type = identification.get("instrument_type", "unknown")
            type_confidence = identification.get("confidence", 0)
            ocr_text = None  # LLM识别时不传OCR文字
            method = "multimodal_identify"
        else:
            type_confidence = 1.0

        logger.info("识别结果: %s (置信度: %s)", instrument_type, type_confidence)

        # 步骤2: 读取数值（OCR文字作为prompt辅助）
        logger.info("步骤2: 使用多模态模型读取数值...")
        mm_readings = self.mm_reader.read_instrument(image_path, instrument_type, ocr_text=ocr_text)

        if "error" in mm_readings:
            return {
                "success": False,
                "error": f"数值读取失败: {mm_readings['error']}"
            }

        # 后处理：修正已知的模型读数偏差
        if instrument_type == "surface_tension_meter":
            if mm_readings.get("f_value") is not None:
                try:
                    mm_readings["f_value"] = abs(float(str(mm_readings["f_value"]).replace(" ", "")))
                except (ValueError, TypeError):
                    pass
            if mm_readings.get("tension") is not None:
                try:
                    mm_readings["tension"] = float(str(mm_readings["tension"]))
                except (ValueError, TypeError):
                    pass

        template = DynamicInstrumentLibrary.get_template(instrument_type)
        instrument_name = template.get("name", "未知仪器") if template else "未知仪器"

        result = {
            "success": True,
            "instrument_type": instrument_type,
            "instrument_name": instrument_name,
            "type_confidence": type_confidence,
            "readings": mm_readings,  # 平铺JSON直接作为readings
            "confidence": 0.9,
            "method": method,
        }

        if result["readings"] and template:
            fields = template.get("fields", [])
            unit_map = {f.get("name"): f.get("unit", "") for f in fields}
            for attr, value in result["readings"].items():
                if value is not None:
                    unit = unit_map.get(attr, "")
                    logger.info("  %s: %s %s", attr, value, unit)

        return result

    def batch_read(self, image_dir: str) -> list:
        """批量读取仪器"""
        image_dir = Path(image_dir)
        image_files = []
        for ext in Config.IMAGE_EXTENSIONS:
            image_files.extend(image_dir.glob(f"*{ext}"))
            image_files.extend(image_dir.glob(f"*{ext.upper()}"))

        results = []
        for image_file in image_files:
            result = self.read_instrument(str(image_file))
            result["image_file"] = image_file.name
            results.append(result)

        return results


def main():
    """主函数"""
    reader = InstrumentReader()

    demo_dir = Path("demo")
    if demo_dir.exists():
        print("\n" + "="*60)
        print("开始批量读取demo文件夹中的仪器")
        print("="*60)

        results = reader.batch_read(str(demo_dir))

        print("\n" + "="*60)
        print("读取完成！结果汇总：")
        print("="*60)

        for result in results:
            print(f"\n图片: {result.get('image_file', 'unknown')}")
            print(f"仪器类型: {result.get('instrument_name', 'unknown')}")
            print(f"识别方法: {result.get('method', 'unknown')}")
            if result["success"]:
                for attr, value in result.get("readings", {}).items():
                    if value is not None:
                        instrument_type = result.get("instrument_type", "")
                        template = DynamicInstrumentLibrary.get_template(instrument_type)
                        if template:
                            fields = template.get("fields", [])
                            unit_map = {f.get("name"): f.get("unit", "") for f in fields}
                            unit = unit_map.get(attr, "")
                            print(f"  {attr}: {value} {unit}")
    else:
        print("demo文件夹不存在，请确保路径正确")


if __name__ == "__main__":
    main()
