"""
基于 Semantic Kernel 的智能体基类定义
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.kernel import Kernel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent

from .message import Message, MessageType


class AgentStatus(Enum):
    """智能体状态枚举"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


class AgentRole(Enum):
    """智能体角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    COORDINATOR = "coordinator"
    OBSERVER = "observer"


class AgentMetadata(BaseModel):
    """智能体元数据"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    role: AgentRole
    description: str = ""
    capabilities: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    tags: List[str] = Field(default_factory=list)


class BaseAgent(ABC):
    """智能体基类
    
    基于 Semantic Kernel 的 ChatCompletionAgent 实现
    """
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        service: ChatCompletionClientBase,
        instructions: str = "",
        description: str = "",
        capabilities: List[str] = None,
        kernel: Optional[Kernel] = None
    ):
        self.metadata = AgentMetadata(
            name=name,
            role=role,
            description=description,
            capabilities=capabilities or []
        )
        self.status = AgentStatus.IDLE
        
        # 初始化 Semantic Kernel 智能体
        self.sk_agent = ChatCompletionAgent(
            service=service,
            name=name,
            instructions=instructions or f"你是一个{role.value}智能体。{description}",
            kernel=kernel
        )
        
        # 消息历史和上下文
        self.chat_history = ChatHistory()
        self.context: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        
    @property
    def id(self) -> str:
        """获取智能体ID"""
        return self.metadata.id
    
    @property
    def name(self) -> str:
        """获取智能体名称"""
        return self.metadata.name
    
    @property
    def role(self) -> AgentRole:
        """获取智能体角色"""
        return self.metadata.role
    
    def set_status(self, status: AgentStatus) -> None:
        """设置智能体状态"""
        self.status = status
    
    def add_message(self, message: Union[Message, str]) -> None:
        """添加消息到历史记录"""
        if isinstance(message, str):
            # 转换为 Semantic Kernel 的消息格式
            chat_message = ChatMessageContent.create(
                role="user",
                content=message
            )
            self.chat_history.add_message(chat_message)
        elif isinstance(message, Message):
            # 转换我们的 Message 为 SK 格式
            role = "assistant" if message.sender_id == self.id else "user"
            chat_message = ChatMessageContent.create(
                role=role,
                content=message.get_text_content()
            )
            self.chat_history.add_message(chat_message)
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文信息"""
        return self.context.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文信息"""
        self.context[key] = value
    
    def register_tool(self, name: str, tool: Any) -> None:
        """注册工具"""
        self.tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[Any]:
        """获取工具"""
        return self.tools.get(name)
    
    async def process_message(self, message: Union[Message, str]) -> Message:
        """处理消息 - 基于 Semantic Kernel"""
        self.set_status(AgentStatus.THINKING)
        
        try:
            # 添加消息到历史
            self.add_message(message)
            
            # 使用 Semantic Kernel 智能体获取响应
            if isinstance(message, str):
                input_message = message
            else:
                input_message = message.get_text_content()
            
            # 调用 SK Agent
            response = await self.sk_agent.invoke(
                chat_history=self.chat_history,
                arguments={"input": input_message}
            )
            
            # 转换为我们的 Message 格式
            response_message = Message(
                type=MessageType.TEXT,
                content=str(response) if response else "无响应",
                sender_id=self.id,
                sender_name=self.name,
                recipient_id=message.sender_id if isinstance(message, Message) else "user",
                recipient_name=message.sender_name if isinstance(message, Message) else "User"
            )
            
            # 添加响应到历史
            self.add_message(response_message)
            self.set_status(AgentStatus.IDLE)
            
            return response_message
            
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            error_message = Message(
                type=MessageType.ERROR,
                content=f"处理失败: {str(e)}",
                sender_id=self.id,
                sender_name=self.name,
                recipient_id=message.sender_id if isinstance(message, Message) else "user",
                recipient_name=message.sender_name if isinstance(message, Message) else "User"
            )
            return error_message
    
    async def think(self, input_data: Any) -> Any:
        """思考处理 - 默认实现"""
        return await self.process_message(str(input_data))
    
    async def act(self, action: Dict[str, Any]) -> Any:
        """执行动作 - 默认实现"""
        action_content = action.get("content", str(action))
        return await self.process_message(action_content)
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.status = AgentStatus.IDLE
        self.chat_history.clear()
        self.context.clear()
    
    def get_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "description": self.metadata.description,
            "capabilities": self.metadata.capabilities,
            "message_count": len(self.chat_history.messages),
            "tools": list(self.tools.keys())
        }
    
    def __str__(self) -> str:
        return f"Agent({self.name}, {self.role.value}, {self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()