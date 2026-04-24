import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BasePostProcessor:
    """后处理器基类"""
    def process(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        corrected = dict(readings)
        # 默认通用处理：将数字形式的字符串安全转换为 float
        for k, v in corrected.items():
            if isinstance(v, str):
                str_val = v.strip()
                # 保留纯数字、小数点、负号
                clean_val = re.sub(r'[^\d\.\-]', '', str_val)
                # 确保不是只有一个小数点或负号
                if clean_val and clean_val not in (".", "-"):
                    try:
                        # 避免转换 "自动"/"手动" 这种纯文本
                        # 只有当原始字符串不包含字母等非数值字符时，才认为它是数字
                        if not re.search(r'[a-zA-Z\u4e00-\u9fa5]', str_val):
                             corrected[k] = float(clean_val)
                    except ValueError:
                        pass
        return corrected

class BalancePostProcessor(BasePostProcessor):
    """天平 (F1, F2) 后处理器：专治小数点漏读"""
    def process(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        # 先执行通用的字符串转浮点
        corrected = super().process(readings)
        for key in ["weight", "reading", "value", "重量"]:
            if key in corrected:
                val = readings[key] # 用原始数据检查字符串里是否有小数点
                if val is not None:
                    str_val = str(val).strip().replace("g", "").replace("G", "").strip()
                    clean_val = re.sub(r'[^\d\.\-]', '', str_val)
                    if not clean_val:
                        continue
                        
                    try:
                        f_val = float(clean_val)
                        # 如果没有小数点（模型漏读了点），强制向左移动两位小数点
                        if "." not in str_val and f_val > 0:
                            # 根据天平特性，通常最后两位是小数 (如 4033 -> 40.33, 842 -> 8.42)
                            new_val = f_val / 100.0
                            logger.info(f"[PostProcess Balance] 强行补齐小数点: {f_val} -> {new_val}")
                            corrected[key] = new_val
                        else:
                            corrected[key] = f_val
                    except Exception as e:
                        logger.warning(f"[PostProcess Balance] 转换错误 {val}: {e}")
        return corrected

class PHMeterPostProcessor(BasePostProcessor):
    """pH计 (F3) 后处理器：修正 pH 值范围"""
    def process(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        corrected = super().process(readings)
        for key in ["ph_value", "PH值"]:
            if key in readings and readings[key] is not None:
                try:
                    str_val = str(readings[key]).strip()
                    clean_val = re.sub(r'[^\d\.\-]', '', str_val)
                    if clean_val:
                        f_val = float(clean_val)
                        # pH 值一般在 0-14 之间，如果读出 673，肯定是漏了点
                        if f_val > 14 and "." not in str_val:
                            new_val = f_val / 100.0
                            logger.info(f"[PostProcess PH] 修正 pH 范围: {f_val} -> {new_val}")
                            corrected[key] = new_val
                        else:
                            corrected[key] = f_val
                except Exception: pass
                
        # 温度一般在 0-100 之间，如果出现 250，大概率是 25.0
        for key in ["temperature", "温度"]:
            if key in readings and readings[key] is not None:
                 try:
                    str_val = str(readings[key]).strip()
                    f_val = float(re.sub(r'[^\d\.\-]', '', str_val))
                    if f_val > 100 and "." not in str_val:
                        new_val = f_val / 10.0
                        logger.info(f"[PostProcess PH] 修正温度范围: {f_val} -> {new_val}")
                        corrected[key] = new_val
                 except Exception: pass
                 
        return corrected

class MixerPostProcessor(BasePostProcessor):
    """混调器 (F0) 及其他涉及时间的后处理器"""
    def process(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        corrected = super().process(readings)
        # 自动将时间字段的 MM:SS 转换为秒
        time_keys = ["total_time", "remaining_time", "seg1_time", "seg2_time", "seg3_time", "high_time", "low_time", "time", "剩余时长", "总共时长", "段一时间", "段二时间", "段三时间", "高速时间", "低速时间"]
        for key in time_keys:
            if key in readings and readings[key] is not None:
                str_val = str(readings[key]).strip()
                if ":" in str_val:
                    try:
                        parts = str_val.split(":")
                        if len(parts) == 2:
                            seconds = float(parts[0]) * 60 + float(parts[1])
                            logger.info(f"[PostProcess Time] 转换时间格式: {str_val} -> {seconds}s")
                            corrected[key] = seconds
                    except Exception: pass
        return corrected

class WaterBathPostProcessor(BasePostProcessor):
    """水浴锅 (F7) 后处理器：修正温度小数点"""
    def process(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        corrected = super().process(readings)
        # 1. 温度修正：最后一位是小数
        for key in ["temperature", "温度"]:
            if key in readings and readings[key] is not None:
                try:
                    str_val = str(readings[key]).strip()
                    clean_val = re.sub(r'[^\d\.\-]', '', str_val)
                    if clean_val:
                        f_val = float(clean_val)
                        # 如果没有小数点，强制把最后一位当做小数 (如 375 -> 37.5)
                        if "." not in str_val:
                            new_val = f_val / 10.0
                            logger.info(f"[PostProcess WaterBath] 修正温度小数点: {f_val} -> {new_val}")
                            corrected[key] = new_val
                        else:
                            corrected[key] = f_val
                except Exception: pass
        
        # 2. 时间修正：水浴锅的时间通常是整数分钟
        for key in ["time", "时间"]:
            if key in readings and readings[key] is not None:
                try:
                    str_val = str(readings[key]).strip()
                    clean_val = re.sub(r'[^\d\.\-]', '', str_val)
                    if clean_val:
                        corrected[key] = float(clean_val)
                except Exception: pass
        return corrected

class TensiometerPostProcessor(BasePostProcessor):
    """表界面张力仪 (F5) 后处理器"""
    def process(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        # 基础处理已经把字符串转为了浮点数，直接返回即可
        return super().process(readings)

# 注册表
POST_PROCESSOR_REGISTRY = {
    "balance": BalancePostProcessor(),
    "ph_meter": PHMeterPostProcessor(),
    "mixer": MixerPostProcessor(),
    "tensiometer": TensiometerPostProcessor(),
    "water_bath": WaterBathPostProcessor(),
    "default": BasePostProcessor() # 默认处理，将字符串转数字
}

def apply_post_processing(class_id: int, readings: Dict[str, Any]) -> Dict[str, Any]:
    """统一的后处理入口"""
    # 从数据库或配置中获取该仪器对应的处理逻辑别名
    from instrument_reader import DynamicInstrumentLibrary
    pp_type = DynamicInstrumentLibrary.get_post_process_type(class_id)
    
    # 兼容旧版的硬编码
    if pp_type == "decimal_correction_2":
        pp_type = "balance"
        
    processor = POST_PROCESSOR_REGISTRY.get(pp_type)
    if processor:
        logger.debug(f"应用 {pp_type} 后处理规则")
        return processor.process(readings)
    
    # 如果数据库没配置，按 ID 做默认降级兜底
    fallback_map = {
        0: "mixer",
        1: "balance",
        2: "balance",
        3: "ph_meter",
        5: "tensiometer",
        6: "mixer", # 包含 time 转换
        7: "water_bath"  # 包含温度小数点转换
    }
    fallback_type = fallback_map.get(class_id)
    if fallback_type and fallback_type in POST_PROCESSOR_REGISTRY:
        logger.debug(f"应用 {fallback_type} 后处理规则 (Fallback)")
        return POST_PROCESSOR_REGISTRY[fallback_type].process(readings)
        
    # 如果没有特定的 fallback，走通用流程把纯数字字符串转为 float
    return POST_PROCESSOR_REGISTRY["default"].process(readings)
