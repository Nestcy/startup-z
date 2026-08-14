from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import logging
import httpx
from langchain_openai import ChatOpenAI

logger = logging.getLogger("startup-stress-test-agent.model")

Message = Dict[str, str]  # {"role": "system|user|assistant", "content": "..."}

class ModelResponse:
    def __init__(self, content: str):
        self.content = content

class ModelClient(ABC):
    @abstractmethod
    async def apredict(self, messages: List[Message]) -> ModelResponse:
        ...

class OpenAIModelClient(ModelClient):
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.0):
        model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = ChatOpenAI(temperature=temperature, model_name=model_name)

    async def apredict(self, messages: List[Message]) -> ModelResponse:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        lc_messages = []
        for m in messages:
            r = m.get("role", "user")
            if r == "system":
                lc_messages.append(SystemMessage(content=m["content"]))
            elif r == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))
            else:
                lc_messages.append(HumanMessage(content=m["content"]))

        resp = await self.client.ainvoke(lc_messages)
        return ModelResponse(content=resp.content)

class GroqModelClient(ModelClient):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, temperature: float = 0.0):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "chat-groq")
        self.base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.ai/v1")
        self.temperature = temperature
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set; Groq client will not function.")

    async def apredict(self, messages: List[Message]) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not configured")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            content = ""
            if "choices" in data and data["choices"]:
                ch = data["choices"][0]
                if isinstance(ch.get("message"), dict):
                    content = ch["message"].get("content", "")
                else:
                    content = ch.get("text", "")
            elif "output" in data and data["output"]:
                content = data["output"][0].get("content", "")
            else:
                content = str(data)
            return ModelResponse(content=content)

# Dependency provider for FastAPI
from fastapi import Depends

def get_model_client() -> ModelClient:
    # prefer Groq if GROQ_API_KEY is present
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        return GroqModelClient(api_key=groq_key, model=os.getenv("GROQ_MODEL"), base_url=os.getenv("GROQ_BASE_URL"))
    # fallback to OpenAI
    return OpenAIModelClient(model_name=os.getenv("OPENAI_MODEL"))
