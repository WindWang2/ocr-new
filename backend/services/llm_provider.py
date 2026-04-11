"""
LLM Provider - OpenAI 兼容 API 后端
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable

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
    max_tokens: int = 500


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
        max_tokens: int = 500,
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
            "chat_template_kwargs": {"enable_thinking": False},
        }

        # 重试逻辑：LMStudio 懒加载时首次请求可能返回 400（worker 未就绪）或超时
        for attempt in range(3):
            try:
                resp = self._http.post(
                    f"{self._base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code == 400 and attempt < 2:
                    logger.warning("LMStudio 返回 400（worker 可能未就绪），等待后重试 (%d/3)…", attempt + 1)
                    time.sleep(3)
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt < 2:
                    logger.warning("请求失败（%s），重试 (%d/3)…", e, attempt + 1)
                    time.sleep(3)
                else:
                    raise

    def close(self):
        self._http.close()


def create_provider(config: LLMConfig) -> LLMProvider:
    """工厂函数：创建 provider 实例"""
    logger.info("创建 OpenAI 兼容 Provider: %s @ %s", config.model_name, config.base_url)
    return OpenAICompatibleProvider(config)


def get_global_provider() -> LLMProvider:
    """获取全局 LLM provider 单例，首次调用时从数据库配置创建"""
    global _global_provider
    if _global_provider is not None:
        return _global_provider

    # 尝试从数据库加载配置
    try:
        from backend.models.database import get_config
        saved = get_config("llm_config", default=None)
        if saved:
            config = LLMConfig(**saved)
        else:
            config = None
    except Exception:
        config = None

    if config is None:
        from config import Config
        config = LLMConfig(
            provider=Config.DEFAULT_LLM_PROVIDER,
            model_name=Config.LMSTUDIO_MODEL,
            base_url=Config.LMSTUDIO_BASE_URL,
            temperature=Config.MODEL_TEMPERATURE,
            max_tokens=Config.MODEL_MAX_TOKENS,
        )

    _global_provider = create_provider(config)
    return _global_provider


def set_global_provider(provider: LLMProvider) -> None:
    """设置全局 LLM provider 单例，关闭旧连接"""
    global _global_provider
    if _global_provider is not None and hasattr(_global_provider, 'close'):
        _global_provider.close()
    _global_provider = provider
