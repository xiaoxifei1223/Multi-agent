"""
LLM 服务接口定义
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel


class LLMRequest(BaseModel):
    """LLM 请求模型"""
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[str] = None


class LLMResponse(BaseModel):
    """LLM 响应模型"""
    content: str
    usage: Dict[str, int]
    finish_reason: str
    function_call: Optional[Dict[str, Any]] = None
    model: str
    created: int


class LLMService(ABC):
    """LLM 服务接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name", "")
        self.is_available = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """聊天补全"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """流式聊天补全"""
        pass
    
    @abstractmethod
    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """函数调用"""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    async def close(self) -> None:
        """关闭服务连接"""
        pass
    
    def __str__(self) -> str:
        return f"LLMService({self.model_name})"