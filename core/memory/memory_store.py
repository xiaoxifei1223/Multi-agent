"""
记忆存储系统
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum
import json


class MemoryType(Enum):
    """记忆类型枚举"""
    SHORT_TERM = "short_term"      # 短期记忆
    LONG_TERM = "long_term"        # 长期记忆
    WORKING = "working"            # 工作记忆
    EPISODIC = "episodic"          # 情景记忆
    SEMANTIC = "semantic"          # 语义记忆
    PROCEDURAL = "procedural"      # 程序记忆


class MemoryImportance(Enum):
    """记忆重要性枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Memory(BaseModel):
    """记忆单元"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: Union[str, Dict[str, Any]]
    memory_type: MemoryType
    importance: MemoryImportance = MemoryImportance.MEDIUM
    owner_id: str                  # 记忆所有者(智能体)ID
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    expires_at: Optional[datetime] = None
    
    def access(self) -> None:
        """访问记忆，更新访问信息"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def is_expired(self) -> bool:
        """检查记忆是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """检查是否有指定标签"""
        return tag in self.tags
    
    def get_content_text(self) -> str:
        """获取文本内容"""
        if isinstance(self.content, str):
            return self.content
        return json.dumps(self.content, ensure_ascii=False)


class MemoryFilter(BaseModel):
    """记忆过滤器"""
    
    memory_types: Optional[List[MemoryType]] = None
    importance_levels: Optional[List[MemoryImportance]] = None
    tags: Optional[List[str]] = None
    owner_ids: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    accessed_after: Optional[datetime] = None
    accessed_before: Optional[datetime] = None
    min_access_count: Optional[int] = None
    max_access_count: Optional[int] = None
    include_expired: bool = False


class MemoryStore:
    """记忆存储管理器"""
    
    def __init__(self, max_memories: int = 10000):
        self.max_memories = max_memories
        self.memories: Dict[str, Memory] = {}
        self._indices = {
            "by_owner": {},      # 按所有者索引
            "by_type": {},       # 按类型索引
            "by_tag": {},        # 按标签索引
            "by_importance": {}  # 按重要性索引
        }
    
    def store_memory(self, memory: Memory) -> str:
        """存储记忆"""
        # 检查容量限制
        if len(self.memories) >= self.max_memories:
            self._cleanup_memories()
        
        # 存储记忆
        self.memories[memory.id] = memory
        
        # 更新索引
        self._update_indices(memory)
        
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        memory = self.memories.get(memory_id)
        if memory and not memory.is_expired():
            memory.access()
            return memory
        elif memory and memory.is_expired():
            # 删除过期记忆
            self.delete_memory(memory_id)
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            del self.memories[memory_id]
            self._remove_from_indices(memory)
            return True
        return False
    
    def search_memories(
        self, 
        query: str = "", 
        filter_criteria: Optional[MemoryFilter] = None,
        limit: int = 50
    ) -> List[Memory]:
        """搜索记忆"""
        results = []
        
        for memory in self.memories.values():
            # 检查过期
            if memory.is_expired() and not (filter_criteria and filter_criteria.include_expired):
                continue
            
            # 应用过滤器
            if filter_criteria and not self._matches_filter(memory, filter_criteria):
                continue
            
            # 简单的文本匹配
            if query:
                content_text = memory.get_content_text().lower()
                if query.lower() not in content_text and not any(query.lower() in tag.lower() for tag in memory.tags):
                    continue
            
            results.append(memory)
        
        # 按重要性和访问时间排序
        results.sort(key=lambda m: (m.importance.value, m.last_accessed), reverse=True)
        
        # 更新访问信息
        for memory in results[:limit]:
            memory.access()
        
        return results[:limit]
    
    def get_memories_by_owner(self, owner_id: str) -> List[Memory]:
        """获取指定所有者的记忆"""
        filter_criteria = MemoryFilter(owner_ids=[owner_id])
        return self.search_memories(filter_criteria=filter_criteria)
    
    def get_memories_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """获取指定类型的记忆"""
        filter_criteria = MemoryFilter(memory_types=[memory_type])
        return self.search_memories(filter_criteria=filter_criteria)
    
    def get_memories_by_tags(self, tags: List[str]) -> List[Memory]:
        """获取包含指定标签的记忆"""
        filter_criteria = MemoryFilter(tags=tags)
        return self.search_memories(filter_criteria=filter_criteria)
    
    def get_recent_memories(self, hours: int = 24, limit: int = 50) -> List[Memory]:
        """获取最近的记忆"""
        since = datetime.now() - timedelta(hours=hours)
        filter_criteria = MemoryFilter(accessed_after=since)
        return self.search_memories(filter_criteria=filter_criteria, limit=limit)
    
    def get_important_memories(self, min_importance: MemoryImportance = MemoryImportance.HIGH) -> List[Memory]:
        """获取重要记忆"""
        importance_levels = [level for level in MemoryImportance if level.value >= min_importance.value]
        filter_criteria = MemoryFilter(importance_levels=importance_levels)
        return self.search_memories(filter_criteria=filter_criteria)
    
    def update_memory_importance(self, memory_id: str, importance: MemoryImportance) -> bool:
        """更新记忆重要性"""
        memory = self.memories.get(memory_id)
        if memory:
            old_importance = memory.importance
            memory.importance = importance
            # 更新重要性索引
            self._update_importance_index(memory, old_importance)
            return True
        return False
    
    def cleanup_expired_memories(self) -> int:
        """清理过期记忆"""
        expired_ids = []
        for memory_id, memory in self.memories.items():
            if memory.is_expired():
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            self.delete_memory(memory_id)
        
        return len(expired_ids)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        total = len(self.memories)
        by_type = {}
        by_importance = {}
        by_owner = {}
        
        for memory in self.memories.values():
            # 按类型统计
            type_name = memory.memory_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            
            # 按重要性统计
            importance_name = memory.importance.name
            by_importance[importance_name] = by_importance.get(importance_name, 0) + 1
            
            # 按所有者统计
            owner = memory.owner_id
            by_owner[owner] = by_owner.get(owner, 0) + 1
        
        return {
            "total_memories": total,
            "max_capacity": self.max_memories,
            "usage_percentage": (total / self.max_memories) * 100,
            "by_type": by_type,
            "by_importance": by_importance,
            "by_owner": by_owner
        }
    
    def _matches_filter(self, memory: Memory, filter_criteria: MemoryFilter) -> bool:
        """检查记忆是否匹配过滤条件"""
        # 检查记忆类型
        if filter_criteria.memory_types and memory.memory_type not in filter_criteria.memory_types:
            return False
        
        # 检查重要性级别
        if filter_criteria.importance_levels and memory.importance not in filter_criteria.importance_levels:
            return False
        
        # 检查标签
        if filter_criteria.tags:
            if not any(tag in memory.tags for tag in filter_criteria.tags):
                return False
        
        # 检查所有者
        if filter_criteria.owner_ids and memory.owner_id not in filter_criteria.owner_ids:
            return False
        
        # 检查创建时间
        if filter_criteria.created_after and memory.created_at < filter_criteria.created_after:
            return False
        if filter_criteria.created_before and memory.created_at > filter_criteria.created_before:
            return False
        
        # 检查访问时间
        if filter_criteria.accessed_after and memory.last_accessed < filter_criteria.accessed_after:
            return False
        if filter_criteria.accessed_before and memory.last_accessed > filter_criteria.accessed_before:
            return False
        
        # 检查访问次数
        if filter_criteria.min_access_count and memory.access_count < filter_criteria.min_access_count:
            return False
        if filter_criteria.max_access_count and memory.access_count > filter_criteria.max_access_count:
            return False
        
        return True
    
    def _update_indices(self, memory: Memory) -> None:
        """更新索引"""
        # 按所有者索引
        if memory.owner_id not in self._indices["by_owner"]:
            self._indices["by_owner"][memory.owner_id] = []
        self._indices["by_owner"][memory.owner_id].append(memory.id)
        
        # 按类型索引
        type_key = memory.memory_type.value
        if type_key not in self._indices["by_type"]:
            self._indices["by_type"][type_key] = []
        self._indices["by_type"][type_key].append(memory.id)
        
        # 按标签索引
        for tag in memory.tags:
            if tag not in self._indices["by_tag"]:
                self._indices["by_tag"][tag] = []
            self._indices["by_tag"][tag].append(memory.id)
        
        # 按重要性索引
        importance_key = memory.importance.name
        if importance_key not in self._indices["by_importance"]:
            self._indices["by_importance"][importance_key] = []
        self._indices["by_importance"][importance_key].append(memory.id)
    
    def _remove_from_indices(self, memory: Memory) -> None:
        """从索引中移除记忆"""
        # 从所有者索引移除
        if memory.owner_id in self._indices["by_owner"]:
            if memory.id in self._indices["by_owner"][memory.owner_id]:
                self._indices["by_owner"][memory.owner_id].remove(memory.id)
        
        # 从类型索引移除
        type_key = memory.memory_type.value
        if type_key in self._indices["by_type"]:
            if memory.id in self._indices["by_type"][type_key]:
                self._indices["by_type"][type_key].remove(memory.id)
        
        # 从标签索引移除
        for tag in memory.tags:
            if tag in self._indices["by_tag"]:
                if memory.id in self._indices["by_tag"][tag]:
                    self._indices["by_tag"][tag].remove(memory.id)
        
        # 从重要性索引移除
        importance_key = memory.importance.name
        if importance_key in self._indices["by_importance"]:
            if memory.id in self._indices["by_importance"][importance_key]:
                self._indices["by_importance"][importance_key].remove(memory.id)
    
    def _update_importance_index(self, memory: Memory, old_importance: MemoryImportance) -> None:
        """更新重要性索引"""
        # 从旧重要性索引移除
        old_key = old_importance.name
        if old_key in self._indices["by_importance"]:
            if memory.id in self._indices["by_importance"][old_key]:
                self._indices["by_importance"][old_key].remove(memory.id)
        
        # 添加到新重要性索引
        new_key = memory.importance.name
        if new_key not in self._indices["by_importance"]:
            self._indices["by_importance"][new_key] = []
        self._indices["by_importance"][new_key].append(memory.id)
    
    def _cleanup_memories(self) -> None:
        """清理记忆以释放空间"""
        # 首先清理过期记忆
        self.cleanup_expired_memories()
        
        # 如果还是超出容量，清理最少访问的低重要性记忆
        if len(self.memories) >= self.max_memories:
            memories_list = list(self.memories.values())
            # 按重要性和访问次数排序，移除最不重要的记忆
            memories_list.sort(key=lambda m: (m.importance.value, m.access_count))
            
            # 移除最旧的10%记忆
            to_remove = int(len(memories_list) * 0.1)
            for memory in memories_list[:to_remove]:
                self.delete_memory(memory.id)