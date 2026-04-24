"""
LLM Provider - OpenAI 兼容 API 后端
"""

import logging
import time
import torch
import json
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProvider(Protocol):
    """LLM 后端接口定义"""
    @property
    def model_name(self) -> str: ...
    @property
    def provider_type(self) -> str: ...
    def chat(
        self,
        messages: List[Dict[str, Any]],
        images: Optional[List[str]] = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str: ...
    def close(self): ...


_global_provider: Optional[LLMProvider] = None


@dataclass
class LLMConfig:
    """运行时 LLM 模型配置"""
    provider: str              # "openai_compatible"
    model_name: str
    base_url: str
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2048


class OpenAICompatibleProvider:
    """OpenAI 兼容 API 后端，使用 httpx 直接调用"""

    def __init__(self, config: LLMConfig):
        import httpx
        self._base_url = config.base_url.rstrip("/")
        self._model_name = config.model_name
        self._api_key = config.api_key or ""
        self._http = httpx.Client(timeout=300.0)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_type(self) -> str:
        return "openai_compatible"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        images: Optional[List[str]] = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
    ) -> str:
        openai_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if msg["role"] == "user" and images:
                content: List[Dict[str, Any]] = [
                    {"type": "text", "text": msg["content"]}
                ]
                for img_b64 in images:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    })
                openai_messages.append({"role": "user", "content": content})
            else:
                openai_messages.append({"role": msg["role"], "content": msg["content"]})

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model_name,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # "chat_template_kwargs": {"enable_thinking": False},
        }

        # 重试逻辑
        for attempt in range(3):
            try:
                resp = self._http.post(
                    f"{self._base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code == 400 and attempt < 2:
                    logger.warning("LMStudio 返回 400，等待后重试 (%d/3)…", attempt + 1)
                    time.sleep(3)
                    continue
                resp.raise_for_status()
                data = resp.json()
                message = data["choices"][0]["message"]
                content = message.get("content") or ""
                # 如果正文为空但有推理内容，尝试使用推理内容（部分模型在推理阶段被截断时会这样）
                if not content and message.get("reasoning_content"):
                    logger.info("Content 为空，使用 reasoning_content")
                    content = message.get("reasoning_content")
                return content
            except Exception as e:
                if attempt < 2:
                    logger.warning("请求失败（%s），重试 (%d/3)…", e, attempt + 1)
                    time.sleep(3)
                else:
                    raise

    def close(self):
        self._http.close()


class TransformersLocalVLMProvider:
    """本地 Transformers VLM 后端 (例如 GLM-OCR)"""

    _model = None
    _processor = None

    def __init__(self, config: LLMConfig):
        self._model_path = config.base_url  # 在 local 模式下 base_url 存的是路径
        self._model_name = config.model_name
        self._config = config

    @classmethod
    def _get_model_and_processor(cls, model_path: str):
        if cls._model is None or cls._processor is None:
            from transformers import AutoModelForImageTextToText, AutoProcessor
            
            # 确保 model_path 是绝对路径且指向本地目录
            abs_model_path = os.path.abspath(model_path)
            if not os.path.isdir(abs_model_path):
                 logger.error(f"VLM 模型目录不存在: {abs_model_path}")
                 # 如果不存在，尝试不转换，让 transformers 自己处理（可能是 repo id）
                 target_path = model_path
            else:
                 target_path = abs_model_path

            logger.info("正在从本地加载 VLM 模型: %s ...", target_path)
            start_time = time.time()
            cls._processor = AutoProcessor.from_pretrained(target_path, trust_remote_code=True)
            cls._model = AutoModelForImageTextToText.from_pretrained(
                target_path,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            logger.info("VLM 模型加载成功, 耗时 %.2f 秒", time.time() - start_time)
            logger.info("模型运行设备: %s", getattr(cls._model, "device", "unknown"))
            if torch.cuda.is_available():
                logger.info("CUDA 已就绪, 当前 GPU: %s", torch.cuda.get_device_name(0))
            else:
                logger.warning("CUDA 不可用, 模型将运行在 CPU 上 (可能非常缓慢)")
        return cls._model, cls._processor

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_type(self) -> str:
        return "local_vlm"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        images: Optional[List[str]] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        print(f"\n[ENGINE_ACTIVE] TransformersLocalVLMProvider starting chat with max_tokens={max_tokens}...")
        import sys; sys.stdout.flush()
        model, processor = self._get_model_and_processor(self._model_path)

        # 准备图片对象
        pil_images = []
        if images:
            for img_b64 in images:
                img_data = base64.b64decode(img_b64)
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                
                # 约束图片尺寸：长边不超过 500 像素，以提升 VLM 推理效率
                max_side = max(img.width, img.height)
                if max_side > 500:
                    scale = 500 / max_side
                    new_size = (int(img.width * scale), int(img.height * scale))
                    # 使用高质量重采样
                    img = img.resize(new_size, Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.BICUBIC)
                    logger.info(f"VLM 输入图片预缩放: {img.width}x{img.height} -> {new_size}")
                
                pil_images.append(img)

        # 构建符合 Transformers 规范的消息结构
        # 注意：这里的 messages 是 MultimodalModelReader 传来的通用格式
        # 我们需要将其转换为适合 apply_chat_template 的格式
        formatted_messages = []
        
        # MultimodalModelReader 传来的通常是:
        # [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        # 但 GLM-OCR 主要是对话式的，我们将 system 融入第一个 user message 或单独处理
        
        user_content = []
        if pil_images:
            for img in pil_images:
                user_content.append({"type": "image", "image": img})
            
        # 合并 system 和 user prompt
        full_text = ""
        for m in messages:
            full_text += m["content"] + "\n"
        
        user_content.append({"type": "text", "text": full_text.strip()})
        
        formatted_messages.append({
            "role": "user",
            "content": user_content
        })

        # 应用模板
        prompt = processor.apply_chat_template(formatted_messages, tokenize=False, add_generation_prompt=True)
        if "<think>" not in prompt:
            prompt += "<think></think>\n"

        # 准备输入
        device = next(model.parameters()).device
        inputs = processor(images=pil_images[0] if pil_images else None, text=prompt, return_tensors="pt").to(device)
        
        # 转换数据类型为 float16
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor) and v.dtype == torch.float:
                inputs[k] = v.to(torch.float16)

        # 生成
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else 1.0, # do_sample为False时忽略
            )
        
        # 解码
        result = processor.decode(output_ids[0], skip_special_tokens=True)
        print(f"\n[DEBUG RAW LLM] >>>\n{result}\n<<< [DEBUG RAW LLM]\n")
        logger.info(f"--- [RAW LLM OUTPUT] ---\n{result}\n-----------------------")
        return result

    def close(self):
        # Local model stays in memory for singleton access
        pass


def create_provider(config: LLMConfig) -> LLMProvider:
    """工厂函数：创建 provider 实例"""
    if config.provider == "local_vlm":
        logger.info("创建本地 VLM Provider (Transformers): %s", config.base_url)
        return TransformersLocalVLMProvider(config)
    
    logger.info("创建 OpenAI 兼容 Provider: %s @ %s", config.model_name, config.base_url)
    return OpenAICompatibleProvider(config)


def get_global_provider() -> LLMProvider:
    """获取全局 LLM provider，支持动态检测配置变更"""
    global _global_provider, _current_config_hash
    
    # 获取当前最新的数据库配置
    try:
        from backend.models.database import get_config
        saved = get_config("llm_config", default=None)
        if not saved:
            from config import Config
            is_local = Config.DEFAULT_LLM_PROVIDER == "local_vlm"
            saved = {
                "provider": Config.DEFAULT_LLM_PROVIDER,
                "model_name": Config.LMSTUDIO_MODEL,
                "base_url": Config.LOCAL_VLM_PATH if is_local else Config.LMSTUDIO_BASE_URL,
                "temperature": Config.MODEL_TEMPERATURE,
                "max_tokens": Config.MODEL_MAX_TOKENS,
            }
    except Exception:
        saved = {}

    # 生成配置指纹，用于判断是否发生变更
    config_hash = hash(json.dumps(saved, sort_keys=True))
    
    if _global_provider is not None:
        # 如果配置没变，直接返回缓存
        if hasattr(get_global_provider, "_last_hash") and get_global_provider._last_hash == config_hash:
            return _global_provider
        else:
            logger.info("检测到 LLM 配置变更，正在更新 Provider...")
            # 如果配置变了，清理旧缓存（对于本地模型可能需要手动触发内存释放，但这里先简单重新实例化）
            _global_provider = None

    # 初始化/重新初始化
    config = LLMConfig(**saved)
    _global_provider = create_provider(config)
    get_global_provider._last_hash = config_hash
    
    return _global_provider


def set_global_provider(provider: LLMProvider) -> None:
    """设置全局 LLM provider 单例，关闭旧连接"""
    global _global_provider
    if _global_provider is not None and hasattr(_global_provider, 'close'):
        _global_provider.close()
    _global_provider = provider
