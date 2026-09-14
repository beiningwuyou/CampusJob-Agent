import os
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LITELLM_TELEMETRY"] = "False"
import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
import litellm
from app.core.config import settings

litellm.telemetry = False

T = TypeVar("T", bound=BaseModel)

class BaseAgent:
    @classmethod
    async def call_structured_llm(
        cls,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T]
    ) -> Optional[T]:
        """统一调用结构化大模型接口 (带本地容错与离线优雅降级)"""
        if not settings.LLM_API_KEY:
            # 当用户暂未配置外部 API Key 时，避免报错崩溃，返回 None 由各 Agent 降级规则处理
            return None

        try:
            # 利用 litellm.acompletion + json_schema
            schema = response_model.model_json_schema()
            response = await litellm.acompletion(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                api_base=settings.LLM_API_BASE,
                messages=[
                    {"role": "system", "content": f"{system_prompt}\n你必须严格遵循以下 JSON Schema 输出规范:\n{json.dumps(schema, ensure_ascii=False)}"},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content
            return response_model.model_validate_json(content)
        except Exception:
            return None

    @classmethod
    async def call_chat_llm(
        cls,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Optional[str]:
        """统一调用对话大模型接口 (用于 Copilot 辅导、深度诊断与智能问答)"""
        if not settings.LLM_API_KEY:
            return None

        try:
            response = await litellm.acompletion(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                api_base=settings.LLM_API_BASE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception:
            return None
