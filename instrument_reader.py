"""
仪器读数识别系统
使用 Ollama 本地部署 Qwen3.5-4B 多模态模型
"""

import os
import sys
import base64
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from config import Config

logger = logging.getLogger(__name__)


class InstrumentLibrary:
    """通用仪器库定义 - 支持多种常见仪器类型"""

    INSTRUMENTS = {
        "electronic_balance": {
            "name": "电子天平/分析天平",
            "attributes": ["weight"],
            "unit": {"weight": "g"},
            "description": "电子或分析天平，用于测量质量，精度通常0.01g-0.0001g",
            "decimal_places": {"weight": 2},
            "display_type": "LCD/LED数码管",
            "keywords": ["天平", "balance", "称重", "质量"]
        },
        "ph_meter": {
            "name": "pH计/酸度计",
            "attributes": ["ph_value", "temperature", "mtc"],
            "unit": {"ph_value": "", "temperature": "°C", "mtc": ""},
            "description": "数字pH计，测量溶液酸碱度，显示温度和MTC温度补偿系数",
            "decimal_places": {"ph_value": 2, "temperature": 1, "mtc": 1},
            "display_type": "LCD背光屏",
            "keywords": ["pH", "酸度", "酸碱度", "PH计", "MTC", "INESA"]
        },
        "ozone_mixer": {
            "name": "臭氧混调器",
            "attributes": ["segment1_speed", "segment1_time", "segment2_speed", "segment2_time", "segment3_speed", "segment3_time", "current_segment", "current_speed"],
            "unit": {"segment1_speed": "rpm", "segment1_time": "s", "segment2_speed": "rpm", "segment2_time": "s", "segment3_speed": "rpm", "segment3_time": "s", "current_segment": "", "current_speed": "rpm"},
            "description": "超级臭氧混调器，屏幕显示段一、段二、段三三个段落的转速和时间参数，以及当前段数和当前转速",
            "decimal_places": {"segment1_speed": 0, "segment1_time": 0, "segment2_speed": 0, "segment2_time": 0, "segment3_speed": 0, "segment3_time": 0, "current_segment": 0, "current_speed": 0},
            "display_type": "触摸式液晶屏",
            "keywords": ["臭氧", "混调器", "超级臭氧", "段一", "段二", "段三", "当前段数", "当前转速", "转速(转)", "时间(S)"]
        },
        "temperature_controller": {
            "name": "温度控制设备",
            "attributes": ["temperature", "time"],
            "unit": {"temperature": "°C", "time": "min"},
            "description": "恒温培养箱、水浴锅、干燥箱等温度控制设备，可能显示温度和定时时间",
            "decimal_places": {"temperature": 1, "time": 0},
            "display_type": "LED数码管/LCD",
            "keywords": ["温度", "恒温", "培养箱", "水浴", "干燥箱", "TEMP", "TIME"]
        },
        "peristaltic_pump": {
            "name": "蠕动泵/计量泵",
            "attributes": ["flow_rate", "rotation_speed"],
            "unit": {"flow_rate": "mL/min", "rotation_speed": "rpm"},
            "description": "蠕动泵、计量泵，用于精确控制液体输送",
            "decimal_places": {"flow_rate": 2, "rotation_speed": 0},
            "display_type": "LCD液晶屏",
            "keywords": ["蠕动泵", "流量", "流速", "泵"]
        },
        "water_quality_meter": {
            "name": "水质检测仪",
            "attributes": ["test_value", "unit"],
            "unit": {"test_value": "", "unit": ""},
            "description": "手持式或台式水质检测仪，可检测多种参数",
            "decimal_places": {"test_value": 2},
            "display_type": "彩色液晶屏",
            "keywords": ["水质", "检测仪", "COD", "总磷", "总氮", "硬度"]
        },
        "centrifuge": {
            "name": "离心机",
            "attributes": ["rotation_speed", "time"],
            "unit": {"rotation_speed": "rpm", "time": "min"},
            "description": "实验室离心机，显示转速和时间",
            "decimal_places": {"rotation_speed": 0, "time": 0},
            "display_type": "触摸式液晶屏",
            "keywords": ["离心", "离心机", "转速", "RPM"]
        },
        "surface_tension_meter": {
            "name": "表面张力仪",
            "attributes": ["surface_tension", "temperature", "rise_speed", "fall_speed", "f_value"],
            "unit": {"surface_tension": "mN/m", "temperature": "°C", "rise_speed": "mm/min", "fall_speed": "mm/min", "f_value": ""},
            "description": "表面张力/界面张力测量仪，显示张力值、温度、升降速度和F值",
            "decimal_places": {"surface_tension": 3, "temperature": 1, "rise_speed": 0, "fall_speed": 0, "f_value": 1},
            "display_type": "触摸屏",
            "keywords": ["表面张力", "界面张力", "F值", "上升速度", "下降速度"]
        },
        "viscometer": {
            "name": "粘度计",
            "attributes": ["viscosity", "temperature"],
            "unit": {"viscosity": "mPa·s", "temperature": "°C"},
            "description": "粘度计，测量流体粘度",
            "decimal_places": {"viscosity": 1, "temperature": 1},
            "display_type": "彩色液晶屏",
            "keywords": ["粘度", "viscosity", "粘度计"]
        },
        "torque_stirrer": {
            "name": "扭矩搅拌器",
            "attributes": ["rotation_speed", "torque", "time"],
            "unit": {"rotation_speed": "rpm", "torque": "N.cm", "time": "s"},
            "description": "扭矩搅拌器，屏幕显示三个数值：上方rpm转速、中间N.cm扭矩、下方时间，没有段一/段二/段三的显示",
            "decimal_places": {"rotation_speed": 0, "torque": 0, "time": 0},
            "display_type": "LED数码管/LCD",
            "keywords": ["扭矩", "搅拌", "N.cm", "rpm", "转速", "扭矩单位"]
        },
        "digital_multimeter": {
            "name": "数字万用表",
            "attributes": ["value", "unit"],
            "unit": {"value": "", "unit": ""},
            "description": "数字万用表，测量电压、电流、电阻等",
            "decimal_places": {"value": 3},
            "display_type": "LCD液晶屏",
            "keywords": ["万用表", "电压", "电流", "电阻", "multimeter"]
        },
        "thermometer": {
            "name": "温度计",
            "attributes": ["temperature"],
            "unit": {"temperature": "°C"},
            "description": "数字温度计或热电偶温度计",
            "decimal_places": {"temperature": 1},
            "display_type": "LCD/LED",
            "keywords": ["温度计", "thermometer", "温度"]
        },
        "hygrometer": {
            "name": "湿度计",
            "attributes": ["humidity", "temperature"],
            "unit": {"humidity": "%RH", "temperature": "°C"},
            "description": "数字湿度计，显示湿度和温度",
            "decimal_places": {"humidity": 1, "temperature": 1},
            "display_type": "LCD液晶屏",
            "keywords": ["湿度", "hygrometer", "RH"]
        },
        "pressure_gauge": {
            "name": "压力表/真空表",
            "attributes": ["pressure"],
            "unit": {"pressure": "MPa/kPa"},
            "description": "数字压力表或真空表",
            "decimal_places": {"pressure": 2},
            "display_type": "LCD/LED",
            "keywords": ["压力", "真空", "pressure", "MPa", "kPa"]
        },
        "conductivity_meter": {
            "name": "电导率仪",
            "attributes": ["conductivity", "temperature"],
            "unit": {"conductivity": "μS/cm", "temperature": "°C"},
            "description": "电导率测量仪，测量溶液电导率",
            "decimal_places": {"conductivity": 1, "temperature": 1},
            "display_type": "LCD液晶屏",
            "keywords": ["电导率", "conductivity", "电导"]
        },
        "dissolved_oxygen_meter": {
            "name": "溶解氧仪",
            "attributes": ["do_value", "temperature"],
            "unit": {"do_value": "mg/L", "temperature": "°C"},
            "description": "溶解氧测量仪，测量水中溶解氧",
            "decimal_places": {"do_value": 2, "temperature": 1},
            "display_type": "LCD液晶屏",
            "keywords": ["溶解氧", "DO", "溶氧"]
        },
        "turbidity_meter": {
            "name": "浊度仪",
            "attributes": ["turbidity"],
            "unit": {"turbidity": "NTU"},
            "description": "浊度测量仪，测量液体浊度",
            "decimal_places": {"turbidity": 2},
            "display_type": "LCD液晶屏",
            "keywords": ["浊度", "turbidity", "NTU"]
        },
        "gas_detector": {
            "name": "气体检测仪",
            "attributes": ["concentration", "gas_type"],
            "unit": {"concentration": "ppm", "gas_type": ""},
            "description": "气体浓度检测仪，检测特定气体浓度",
            "decimal_places": {"concentration": 0},
            "display_type": "LCD/LED",
            "keywords": ["气体", "检测", "ppm", "气体检测仪"]
        },
        "unknown": {
            "name": "未知仪器",
            "attributes": ["value"],
            "unit": {"value": ""},
            "description": "未能识别的仪器类型，尝试读取显示的数值",
            "decimal_places": {"value": 2},
            "display_type": "未知",
            "keywords": []
        }
    }

    @classmethod
    def get_instrument_prompt(cls, instrument_type: str) -> str:
        """获取特定仪器的读取prompt"""
        if instrument_type not in cls.INSTRUMENTS:
            return ""

        instrument = cls.INSTRUMENTS[instrument_type]
        attributes_desc = "、".join([f"{attr}({instrument['unit'].get(attr, '')})"
                                     for attr in instrument['attributes']])

        # 构建示例 readings 对象
        readings_example = ", ".join([f'"{attr}": 0.0' for attr in instrument['attributes']])

        # 针对温度控制器添加特殊说明
        special_note = ""
        if instrument_type == "temperature_controller":
            special_note = """
特别注意：
- LED数码管显示屏上的小数点非常小，只是一个微小的点，很容易被忽略
- 温度显示通常带1位小数，请仔细寻找数字之间的小数点
- 例如：显示"17.3"时，小数点在7和3之间，是一个很小的亮点
- 如果看到3位数字如"173"，请仔细检查中间是否有小数点，实际可能是"17.3"
- 时间显示通常是整数分钟
- TEMP标签下方是温度，TIME标签下方是时间"""
        elif instrument_type == "ph_meter":
            special_note = """
特别注意：
- pH值通常显示2位小数，位于屏幕主要位置
- 温度通常显示1位小数，单位°C
- MTC是温度补偿系数，通常显示在屏幕下方或角落，数值可能是100.0
- 请读取所有三个数值：ph_value、temperature、mtc"""
        elif instrument_type == "ozone_mixer":
            special_note = """
特别注意：
- 读取段一参数：转速(segment1_speed)和时间(segment1_time)
- 读取段二参数：转速(segment2_speed)和时间(segment2_time)
- 读取段三参数：转速(segment3_speed)和时间(segment3_time)
- 读取当前段数(current_segment)和当前转速(current_speed)
- 转速单位是rpm，时间单位是秒"""
        elif instrument_type == "surface_tension_meter":
            special_note = """
特别注意：
- 表面张力(surface_tension)通常带3位小数，可能为负数
- 温度(temperature)可能显示为N/A，如果是N/A则设为null
- 上升速度(rise_speed)和下降速度(fall_speed)单位是mm/min
- F值(f_value)旁边的-和+是调节按钮，不是正负号，F值本身是正数
- 请读取所有五个数值"""
        elif instrument_type == "torque_stirrer":
            special_note = """
特别注意：
- 三个读数：转速(rotation_speed)单位rpm、扭矩(torque)单位N.cm、时间(time)
- 扭矩显示可能是00，表示0 N.cm
- 时间格式可能是MM:SS，需要转换为秒数"""

        prompt = f"""这是{instrument['name']}，读取显示数值：{attributes_desc}
{special_note}
【重要】你必须严格按照以下JSON格式输出，不要输出任何其他内容：

{{"instrument_type": "{instrument_type}", "readings": {{{readings_example}}}, "confidence": 0.95}}

输出要求：
1. 只输出一行JSON，不要有其他任何文字
2. 不要输出分析过程
3. 数值是纯数字，不含单位
4. 无法读取的值设为null
5. 注意观察小数点的位置，不要遗漏

/no_think"""

        return prompt

    @classmethod
    def identify_instrument_prompt(cls) -> str:
        """获取仪器类型识别的prompt"""
        instruments_desc = "\n".join([
            f"- {k}: {v['name']} - {v['description']}"
            for k, v in cls.INSTRUMENTS.items()
        ])

        prompt = f"""识别图片中的仪器类型，从以下选项中选择最匹配的一个：

{instruments_desc}

【重要】你必须严格按照以下JSON格式输出，不要输出任何其他内容（不要分析、不要解释、不要思考过程）：

{{"instrument_type": "选中的仪器类型标识", "confidence": 0.95}}

输出要求：
1. 只输出一行JSON，不要有其他任何文字
2. 不要使用Markdown代码块
3. 不要输出分析过程
4. instrument_type 必须是上述选项之一

/no_think"""

        return prompt


class MultimodalModelReader:
    """多模态大模型读取器（Ollama 后端）"""

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
            self.base_url = base_url or Config.OLLAMA_BASE_URL
            self.model_name = model_name or Config.OLLAMA_QWEN_MODEL

            from backend.services.llm_provider import OllamaProvider, LLMConfig
            self._provider = OllamaProvider(LLMConfig(
                provider="ollama",
                model_name=self.model_name,
                base_url=self.base_url,
            ))

        logger.info("使用 LLM 后端, 模型: %s", self.model_name)

    def encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_image(self, image_path: str, prompt: str, call_type: str = "unknown") -> Dict[str, Any]:
        """使用多模态模型分析图片

        Args:
            image_path: 图片路径
            prompt: 提示词
            call_type: 调用类型（identify/read），用于保存调试文件
        """
        try:
            # 读取图片并转换为 base64
            with open(image_path, "rb") as f:
                image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # 调用 LLM Provider
            result_text = self._provider.chat(
                messages=[{"role": "user", "content": prompt}],
                images=[base64_image],
                temperature=Config.MODEL_TEMPERATURE,
                max_tokens=Config.MODEL_MAX_TOKENS,
            )
            logger.debug("Ollama 模型原始响应: %s", result_text[:500] if len(result_text) > 500 else result_text)

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
        """识别仪器类型"""
        prompt = InstrumentLibrary.identify_instrument_prompt()
        return self.analyze_image(image_path, prompt, call_type="identify")

    def read_instrument(self, image_path: str, instrument_type: str) -> Dict[str, Any]:
        """读取仪器数值"""
        prompt = InstrumentLibrary.get_instrument_prompt(instrument_type)
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
            logger.info("后端: Ollama")
            logger.info("模型: %s", model_name or Config.OLLAMA_QWEN_MODEL)
            self.mm_reader = MultimodalModelReader(model_name=model_name)

        logger.info("系统初始化完成！")

    def read_instrument(self, image_path: str) -> Dict[str, Any]:
        """
        读取仪器读数
        Args:
            image_path: 图片路径
        Returns:
            包含识别结果的字典
        """
        logger.info("处理图片: %s", image_path)

        # 步骤1: 识别仪器类型
        logger.info("步骤1: 使用多模态模型识别仪器类型...")
        identification = self.mm_reader.identify_instrument(image_path)

        if "error" in identification:
            return {
                "success": False,
                "error": f"仪器类型识别失败: {identification['error']}"
            }

        instrument_type = identification.get("instrument_type", "unknown")
        type_confidence = identification.get("confidence", 0)
        logger.info("识别结果: %s (置信度: %s)", instrument_type, type_confidence)

        # 步骤2: 读取数值
        logger.info("步骤2: 使用多模态模型读取数值...")
        mm_readings = self.mm_reader.read_instrument(image_path, instrument_type)

        if "error" in mm_readings:
            return {
                "success": False,
                "error": f"数值读取失败: {mm_readings['error']}"
            }

        # 构建结果
        instrument_info = InstrumentLibrary.INSTRUMENTS.get(instrument_type, {})
        result = {
            "success": True,
            "instrument_type": instrument_type,
            "instrument_name": instrument_info.get("name", "未知仪器"),
            "type_confidence": type_confidence,
            "readings": mm_readings.get("readings", {}),
            "confidence": mm_readings.get("confidence", 0.9),
            "method": "multimodal"
        }

        # 打印结果
        if result["readings"]:
            for attr, value in result["readings"].items():
                if value is not None and instrument_type in InstrumentLibrary.INSTRUMENTS:
                    unit = InstrumentLibrary.INSTRUMENTS[instrument_type]["unit"].get(attr, "")
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
                        if instrument_type in InstrumentLibrary.INSTRUMENTS:
                            unit = InstrumentLibrary.INSTRUMENTS[instrument_type]["unit"].get(attr, "")
                            print(f"  {attr}: {value} {unit}")
    else:
        print("demo文件夹不存在，请确保路径正确")


if __name__ == "__main__":
    main()
