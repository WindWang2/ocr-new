"""
仪器读数识别系统
使用 LMStudio 本地部署多模态模型（OpenAI 兼容 API）
相机配置来源：相机.xlsx
"""

import os
import base64
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)


from backend.models.database import get_all_templates, get_template

class DynamicInstrumentLibrary:
    @classmethod
    def get_template(cls, instrument_type):
        t = get_template(instrument_type)
        if t:
            t['fields'] = json.loads(t['fields_json'])
            t['keywords'] = json.loads(t['keywords_json'])
            t['example_images'] = json.loads(t['example_images_json'] or '[]')
        return t

    @classmethod
    def get_all(cls):
        templates = get_all_templates()
        for t in templates:
            t['fields'] = json.loads(t['fields_json'])
            t['keywords'] = json.loads(t['keywords_json'])
            t['example_images'] = json.loads(t['example_images_json'] or '[]')
        return templates

    @classmethod
    def identify_by_ocr_keywords(cls, ocr_text: str) -> str:
        templates = cls.get_all()
        for t in templates:
            if all(kw in ocr_text for kw in t['keywords']):
                return t['instrument_type']
        return "unknown"

    @classmethod
    def get_instrument_prompt(cls, instrument_type: str) -> str:
        t = cls.get_template(instrument_type)
        if t:
            return t['prompt_template']
        return ""

    # 相机编号到仪器的映射（来源：相机.xlsx）
    CAMERA_PROMPTS = {
        "F0": """这是超级吴英混调器（SN: 258795）控制屏幕。请先判断当前是自动模式还是手动模式（看左侧菜单哪个选项高亮），然后读取对应数值。

自动模式字段：seg1_speed(段一转速,转)、seg1_time(段一时间,S)、seg2_speed(段二转速,转)、seg2_time(段二时间,S)、seg3_speed(段三转速,转)、seg3_time(段三时间,S)、total_time(总时长,S)、remaining_time(剩余时长,S)、current_segment(当前段数)、current_speed(当前转速,转)

手动模式：屏幕中间有一个表格，列标题为"转速(转)"和"时间(S)"，两行分别为"高速"和"低速"。从表格中读取：
- high_speed = "高速"行、"转速(转)"列的数字
- high_time = "高速"行、"时间(S)"列的数字
- low_speed = "低速"行、"转速(转)"列的数字
- low_time = "低速"行、"时间(S)"列的数字
表格下方还有：remaining_time(剩余时间,S)、current_speed(当前转速,转)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：

自动模式：{"mode": "auto", "seg1_speed": 0, "seg1_time": 0, "seg2_speed": 0, "seg2_time": 0, "seg3_speed": 0, "seg3_time": 0, "total_time": 0, "remaining_time": 0, "current_segment": 0, "current_speed": 0}
手动模式：{"mode": "manual", "high_speed": 0, "high_time": 0, "low_speed": 0, "low_time": 0, "remaining_time": 0, "current_speed": 0}

只输出一行JSON，数值为纯数字不含单位，无法读取的值设为null。
""",
        "F1": """这是电子天枰1号（SN: 53662），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g，只输出纯数字不含单位。
""",
        "F2": """这是电子天枰2号（SN: 230199），读取屏幕显示的重量数值。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"weight": 0.00}

注意：仔细辨认小数点位置（LED数码管上小数点很小），数值单位为g，只输出纯数字不含单位。
""",
        "F3": """这是PH仪（SN: 176585），读取屏幕上的三个数值：pH值(ph_value)、温度(temperature,°C,MTC)、PTS值(pts,%PTS)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"ph_value": 0.00, "temperature": 0.0, "pts": 0.0}

注意：pH值通常带2位小数，温度带1位小数，PTS通常为100.0。只输出一行JSON，数值不含单位，无法读取设为null。
""",
        "F4": """这是水质检测仪（SN: 43373），检测总硬度。请先判断当前是高量程还是低量程模式，然后读取屏幕显示的所有数值。

读数字段：当前量程模式(mode)、检测日期(date)、空白值(blank_value)、检测值(test_value)、吸光度(absorbance)、含量mg/L(content_mg_l)、透光度%(transmittance)

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"mode": "high", "date": "", "blank_value": 0, "test_value": 0, "absorbance": 0.000, "content_mg_l": 0.00, "transmittance": 0.0}

注意：mode字段为"high"（高量程）或"low"（低量程），date字段为字符串（格式xxxx-xx-xx xx:xx:xx），其他字段为数值，无法读取设为null。只输出一行JSON。
""",
        "F5": """这是表界面张力仪（SN: 101663），读取屏幕上的六个数值：表/界面张力(tension,nN/m)、温度(temperature,°C)、上层密度(upper_density,g/cm3)、下层密度(lower_density,g/cm3)、上升速度(rise_speed,mm/min)、下降速度(fall_speed,mm/min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"tension": 0.000, "temperature": 0.0, "upper_density": 0.000, "lower_density": 0.000, "rise_speed": 0, "fall_speed": 0}

注意：张力通常带3位小数，可能为负数；温度若显示N/A则设为null；F值旁的-/+是按钮不是正负号。只输出一行JSON，数值不含单位。
""",
        "F6": """这是电动搅拌器（SN: 208721），屏幕显示三行数值：第一行转速(rotation_speed,rpm)、第二行张力(torque,N/cm)、第三行时间(time,XX:XX)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"rotation_speed": 0, "torque": 0, "time": "00:00"}

注意：time字段保留MM:SS字符串格式；torque可能显示为00表示0N/cm。只输出一行JSON，数值不含单位。
""",
        "F7": """这是水浴锅（SN: 37844），读取屏幕显示的温度(temperature,°C)和定时时间(time,min)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"temperature": 0.0, "time": 0}

注意：TEMP标签下方为温度（通常带1位小数，LED数码管小数点很小，如"17.3"），TIME标签下方为时间（整数分钟）。只输出一行JSON，数值不含单位。
""",
        "F8": """这是6速旋转粘度计（SN: 106833），读取屏幕上的八个数值：实施读数(actual_reading)、最大读数(max_reading)、最小读数(min_reading)、转速(rotation_speed,RPM)、剪切速率(shear_rate,S-1)、剪切应力(shear_stress,Pa)、表观粘度(apparent_viscosity,mpa.s)、5秒平均值(avg_5s,mpa.s)。

【重要】严格按以下JSON格式输出，不要输出任何其他内容：
{"actual_reading": 0, "max_reading": 0, "min_reading": 0, "rotation_speed": 0, "shear_rate": 0, "shear_stress": 0.000, "apparent_viscosity": 0.0, "avg_5s": 0.0}

只输出一行JSON，数值不含单位，无法读取设为null。
""",
    }

    CAMERA_INSTRUMENT_NAMES = {
        "F0": "超级吴英混调器",
        "F1": "电子天枰1号",
        "F2": "电子天枰2号",
        "F3": "PH仪",
        "F4": "水质检测仪",
        "F5": "表界面张力仪",
        "F6": "电动搅拌器",
        "F7": "水浴锅",
        "F8": "6速旋转粘度计",
    }

    @classmethod
    def get_camera_prompt(cls, camera_name: str) -> str:
        return cls.CAMERA_PROMPTS.get(camera_name.upper(), "")

    @classmethod
    def get_instrument_type_from_camera(cls, camera_name: str, parsed: dict) -> str:
        static_map = {
            "F1": "electronic_balance",
            "F2": "electronic_balance",
            "F3": "ph_meter",
            "F4": "water_quality_meter",
            "F5": "surface_tension_meter",
            "F6": "torque_stirrer",
            "F7": "temperature_controller",
            "F8": "viscometer_6speed",
        }
        if camera_name in static_map:
            return static_map[camera_name]
        if camera_name == "F0":
            mode = parsed.get("mode", "auto")
            return "wuying_mixer_auto" if mode == "auto" else "wuying_mixer_manual"
        return camera_name.lower()

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
    """多模态大模型读取器（LMStudio 后端）"""

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
            self.base_url = base_url or Config.LMSTUDIO_BASE_URL
            self.model_name = model_name or Config.LMSTUDIO_MODEL

            from backend.services.llm_provider import create_provider, LLMConfig
            self._provider = create_provider(LLMConfig(
                provider=Config.DEFAULT_LLM_PROVIDER,
                model_name=self.model_name,
                base_url=self.base_url,
            ))

        logger.info("使用 LLM 后端, 模型: %s", self.model_name)

    def analyze_image(self, image_path: str, prompt: str, call_type: str = "unknown") -> Dict[str, Any]:
        """使用多模态模型分析图片

        Args:
            image_path: 图片路径
            prompt: 提示词
            call_type: 调用类型（identify/read），用于保存调试文件
        """
        try:
            # 读取图片，统一转为 RGB JPEG 发送（兼容灰度图、BMP 等格式）
            from PIL import Image
            import io
            img = Image.open(image_path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            image_data = buf.getvalue()
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # 调用 LLM Provider
            result_text = self._provider.chat(
                messages=[{"role": "user", "content": prompt}],
                images=[base64_image],
                temperature=Config.MODEL_TEMPERATURE,
                max_tokens=Config.MODEL_MAX_TOKENS,
            )
            logger.debug("模型原始响应: %s", result_text[:500] if len(result_text) > 500 else result_text)

            parsed = self._parse_json_response(result_text)
            if "error" in parsed:
                logger.warning("JSON解析失败，原始响应: %s", result_text)

            # 保存响应到JSON文件（调试用）
            self._save_response_debug(image_path, call_type, prompt, result_text, parsed)

            return parsed
        except Exception as e:
            logger.error("多模态模型分析失败: %s", e)
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """解析JSON响应（支持嵌套JSON、Markdown代码块）"""
        # 清理文本
        text = text.strip()

        # 移除省略号 ...
        text = re.sub(r',\s*\.\.\.\s*', '', text)
        text = re.sub(r'\.\.\.', '', text)

        # 尝试提取 Markdown 代码块中的 JSON
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block_match:
            json_text = code_block_match.group(1).strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass

        try:
            # 先尝试直接解析整个文本
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        try:
            # 提取最外层的 JSON 对象（支持嵌套大括号）
            start = text.find('{')
            if start == -1:
                logger.warning("响应中未找到JSON对象: %s", text[:200])
                return {"error": "响应中未找到JSON对象", "raw_text": text}

            depth = 0
            # 优先从后往前找最后一个完整的JSON对象
            for i in range(len(text) - 1, start - 1, -1):
                if text[i] == '}':
                    # 从start到i检查是否是完整JSON
                    json_str = text[start:i + 1]
                    # 验证大括号匹配
                    depth_check = 0
                    valid = True
                    for c in json_str:
                        if c == '{':
                            depth_check += 1
                        elif c == '}':
                            depth_check -= 1
                            if depth_check < 0:
                                valid = False
                                break
                    if valid and depth_check == 0:
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            pass

            # 如果上面失败，使用原来的方法
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        json_str = text[start:i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.warning("JSON解析错误: %s, JSON内容: %s", e, json_str[:200])
                            return {"error": f"JSON解析错误: {e}", "raw_text": text}
            logger.warning("JSON对象未正确闭合: %s", text[:200])
            return {"error": "JSON对象未正确闭合", "raw_text": text}
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
        return self.analyze_image(image_path, prompt, call_type="read")


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
            logger.info("后端: LMStudio")
            logger.info("模型: %s", model_name or Config.LMSTUDIO_MODEL)
            self.mm_reader = MultimodalModelReader(model_name=model_name)

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

    def read_instrument(self, image_path: str, camera_name: str = None) -> Dict[str, Any]:
        """
        读取仪器读数。
        若能确定相机名称（F0-F8），直接使用相机专用prompt（单步）；
        否则退回两步识别流程。

        Args:
            image_path: 图片路径
            camera_name: 可选，相机名称如 "F0"。为 None 时自动从路径推断。
        Returns:
            包含识别结果的字典
        """
        logger.info("处理图片: %s", image_path)

        # 尝试确定相机名称
        if camera_name is None:
            camera_name = self._extract_camera_name(image_path)

        if camera_name and camera_name.upper() in DynamicInstrumentLibrary.CAMERA_PROMPTS:
            return self._read_by_camera(image_path, camera_name.upper())
        else:
            return self._read_by_identification(image_path)

    def _read_by_camera(self, image_path: str, camera_name: str) -> Dict[str, Any]:
        """使用相机专用prompt直接读取（单步，跳过识别）"""
        logger.info("相机 %s: 使用专用prompt直接读取", camera_name)

        prompt = DynamicInstrumentLibrary.get_camera_prompt(camera_name)
        parsed = self.mm_reader.analyze_image(image_path, prompt, call_type="read")

        if "error" in parsed:
            return {"success": False, "error": f"数值读取失败: {parsed['error']}"}

        instrument_type = DynamicInstrumentLibrary.get_instrument_type_from_camera(camera_name, parsed)
        instrument_name = DynamicInstrumentLibrary.CAMERA_INSTRUMENT_NAMES.get(camera_name, camera_name)
        readings = parsed  # 平铺JSON直接作为readings

        result = {
            "success": True,
            "instrument_type": instrument_type,
            "instrument_name": instrument_name,
            "camera_name": camera_name,
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
        try:
            import httpx
            from PIL import Image
            import io as _io
            img = Image.open(image_path).convert("RGB")
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
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
                timeout=60,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("OCR提取失败: %s", e)
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
