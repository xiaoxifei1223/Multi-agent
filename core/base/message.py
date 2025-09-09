"""
消息系统定义
"""
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"
    NOTIFICATION = "notification"


class MessagePriority(Enum):
    """消息优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Message(BaseModel):
    """消息类"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType
    content: Union[str, Dict[str, Any], List[Any]]
    sender_id: str
    sender_name: str
    recipient_id: Optional[str] = None
    recipient_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_message_id: Optional[str] = None
    thread_id: Optional[str] = None
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)
    
    def is_from(self, sender_id: str) -> bool:
        """检查是否来自指定发送者"""
        return self.sender_id == sender_id
    
    def is_to(self, recipient_id: str) -> bool:
        """检查是否发送给指定接收者"""
        return self.recipient_id == recipient_id
    
    def is_broadcast(self) -> bool:
        """检查是否为广播消息"""
        return self.recipient_id is None
    
    def get_text_content(self) -> str:
        """获取文本内容"""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, dict):
            return self.content.get("text", str(self.content))
        else:
            return str(self.content)
    
    def clone(self) -> "Message":
        """克隆消息"""
        return Message(
            type=self.type,
            content=self.content,
            sender_id=self.sender_id,
            sender_name=self.sender_name,
            recipient_id=self.recipient_id,
            recipient_name=self.recipient_name,
            priority=self.priority,
            metadata=self.metadata.copy(),
            parent_message_id=self.parent_message_id,
            thread_id=self.thread_id
        )
    
    class Config:
        use_enum_values = True


class MessageBuilder:
    """消息构建器"""
    
    def __init__(self):
        self._message_data = {}
    
    def type(self, msg_type: MessageType) -> "MessageBuilder":
        """设置消息类型"""
        self._message_data["type"] = msg_type
        return self
    
    def content(self, content: Union[str, Dict[str, Any], List[Any]]) -> "MessageBuilder":
        """设置消息内容"""
        self._message_data["content"] = content
        return self
    
    def sender(self, sender_id: str, sender_name: str) -> "MessageBuilder":
        """设置发送者"""
        self._message_data["sender_id"] = sender_id
        self._message_data["sender_name"] = sender_name
        return self
    
    def recipient(self, recipient_id: str, recipient_name: str) -> "MessageBuilder":
        """设置接收者"""
        self._message_data["recipient_id"] = recipient_id
        self._message_data["recipient_name"] = recipient_name
        return self
    
    def priority(self, priority: MessagePriority) -> "MessageBuilder":
        """设置优先级"""
        self._message_data["priority"] = priority
        return self
    
    def metadata(self, metadata: Dict[str, Any]) -> "MessageBuilder":
        """设置元数据"""
        self._message_data["metadata"] = metadata
        return self
    
    def thread(self, thread_id: str) -> "MessageBuilder":
        """设置线程ID"""
        self._message_data["thread_id"] = thread_id
        return self
    
    def parent(self, parent_message_id: str) -> "MessageBuilder":
        """设置父消息ID"""
        self._message_data["parent_message_id"] = parent_message_id
        return self
    
    def build(self) -> Message:
        """构建消息"""
        return Message(**self._message_data)


class MessageQueue:
    """消息队列"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._messages: List[Message] = []
    
    def put(self, message: Message) -> None:
        """添加消息到队列"""
        if len(self._messages) >= self.max_size:
            # 移除最旧的消息
            self._messages.pop(0)
        
        # 按优先级插入
        inserted = False
        for i, msg in enumerate(self._messages):
            if message.priority.value > msg.priority.value:
                self._messages.insert(i, message)
                inserted = True
                break
        
        if not inserted:
            self._messages.append(message)
    
    def get(self) -> Optional[Message]:
        """从队列获取消息"""
        if self._messages:
            return self._messages.pop(0)
        return None
    
    def peek(self) -> Optional[Message]:
        """查看队列头部消息但不移除"""
        if self._messages:
            return self._messages[0]
        return None
    
    def size(self) -> int:
        """获取队列大小"""
        return len(self._messages)
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self._messages) == 0
    
    def clear(self) -> None:
        """清空队列"""
        self._messages.clear()
    
    def get_messages_by_sender(self, sender_id: str) -> List[Message]:
        """获取指定发送者的消息"""
        return [msg for msg in self._messages if msg.sender_id == sender_id]
    
    def get_messages_by_type(self, msg_type: MessageType) -> List[Message]:
        """获取指定类型的消息"""
        return [msg for msg in self._messages if msg.type == msg_type]