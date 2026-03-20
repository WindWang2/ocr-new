"""
LLM Provider 抽象层 - 支持 Ollama 和 OpenAI 兼容 API
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_global_provider: Optional["LLMProvider"] = None


@dataclass
class LLMConfig:
    """运行时 LLM 模型配置"""
    provider: str              # "ollama" | "openai_compatible"
    model_name: str
    base_url: str
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 500


class OllamaProvider:
    """Ollama 后端，使用 ollama Python SDK"""

    def __init__(self, config: LLMConfig):
        import ollama
        self._client = ollama.Client(host=config.base_url)
        self._model_name = config.model_name
        self._base_url = config.base_url

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_type(self) -> str:
        return "ollama"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        images: Optional[List[str]] = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        ollama_messages = []
        for msg in messages:
            entry: Dict[str, Any] = {"role": msg["role"], "content": msg["content"]}
            if msg["role"] == "user" and images:
                entry["images"] = images
            ollama_messages.append(entry)

        response = self._client.chat(
            model=self._model_name,
            messages=ollama_messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        return response.message.content


class OpenAICompatibleProvider:
    """OpenAI 兼容 API 后端，使用 httpx 直接调用"""

    def __init__(self, config: LLMConfig):
        import httpx
        self._base_url = config.base_url.rstrip("/")
        self._model_name = config.model_name
        self._api_key = config.api_key or ""
        self._http = httpx.Client(timeout=120.0)

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

        resp = self._http.post(
            f"{self._base_url}/v1/chat/completions",
            headers=headers,
            json={
                "model": self._model_name,
                "messages": openai_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def create_provider(config: LLMConfig) -> "LLMProvider":
    """工厂函数：根据配置创建 provider 实例"""
    if config.provider == "openai_compatible":
        logger.info("创建 OpenAI 兼容 Provider: %s @ %s", config.model_name, config.base_url)
        return OpenAICompatibleProvider(config)
    logger.info("创建 Ollama Provider: %s @ %s", config.model_name, config.base_url)
    return OllamaProvider(config)


def get_global_provider() -> "LLMProvider":
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
            provider="ollama",
            model_name=Config.OLLAMA_QWEN_MODEL,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=Config.MODEL_TEMPERATURE,
            max_tokens=Config.MODEL_MAX_TOKENS,
        )

    _global_provider = create_provider(config)
    return _global_provider


def set_global_provider(provider: "LLMProvider") -> None:
    """设置全局 LLM provider 单例"""
    global _global_provider
    _global_provider = provider
