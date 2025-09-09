"""
智能体范式基类定义
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from enum import Enum
from pydantic import BaseModel

from .agent import BaseAgent
from .message import Message


class PatternType(Enum):
    """范式类型枚举"""
    REFLECTION = "reflection"
    TOOL_USE = "tool_use"
    PLANNING = "planning"
    COLLABORATION = "collaboration"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    DEMOCRACY = "democracy"
    COMPETITIVE = "competitive"


class PatternConfig(BaseModel):
    """范式配置基类"""
    name: str
    description: str = ""
    enabled: bool = True
    parameters: Dict[str, Any] = {}


class BasePattern(ABC):
    """智能体范式基类
    
    定义了所有范式的通用接口和基本功能
    """
    
    def __init__(
        self,
        pattern_type: PatternType,
        config: PatternConfig,
        agents: List[BaseAgent] = None
    ):
        self.pattern_type = pattern_type
        self.config = config
        self.agents: List[BaseAgent] = agents or []
        self.is_active = False
        self.execution_context: Dict[str, Any] = {}
        
    @property
    def name(self) -> str:
        """获取范式名称"""
        return self.config.name
    
    @property
    def type(self) -> PatternType:
        """获取范式类型"""
        return self.pattern_type
    
    def add_agent(self, agent: BaseAgent) -> None:
        """添加智能体到范式"""
        if agent not in self.agents:
            self.agents.append(agent)
    
    def remove_agent(self, agent: BaseAgent) -> None:
        """从范式中移除智能体"""
        if agent in self.agents:
            self.agents.remove(agent)
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """根据名称获取智能体"""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def get_agent_by_role(self, role: str) -> List[BaseAgent]:
        """根据角色获取智能体列表"""
        return [agent for agent in self.agents if agent.role.value == role]
    
    def activate(self) -> None:
        """激活范式"""
        self.is_active = True
        self._on_activate()
    
    def deactivate(self) -> None:
        """停用范式"""
        self.is_active = False
        self._on_deactivate()
    
    def _on_activate(self) -> None:
        """范式激活时的回调"""
        pass
    
    def _on_deactivate(self) -> None:
        """范式停用时的回调"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """执行范式 - 子类必须实现"""
        pass
    
    @abstractmethod
    async def coordinate_agents(self, task: Any) -> Any:
        """协调智能体 - 子类必须实现"""
        pass
    
    def validate_configuration(self) -> bool:
        """验证配置是否正确"""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取范式状态"""
        return {
            "name": self.name,
            "type": self.type.value,
            "is_active": self.is_active,
            "agent_count": len(self.agents),
            "agents": [agent.get_info() for agent in self.agents],
            "config": self.config.dict()
        }
    
    def reset(self) -> None:
        """重置范式状态"""
        self.is_active = False
        self.execution_context.clear()
        for agent in self.agents:
            agent.reset()
    
    def __str__(self) -> str:
        return f"Pattern({self.name}, {self.type.value}, agents={len(self.agents)})"
    
    def __repr__(self) -> str:
        return self.__str__()