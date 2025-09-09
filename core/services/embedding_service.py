"""
嵌入服务接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np


class EmbeddingRequest(BaseModel):
    """嵌入请求模型"""
    texts: List[str]
    model: Optional[str] = None


class EmbeddingResponse(BaseModel):
    """嵌入响应模型"""
    embeddings: List[List[float]]
    usage: Dict[str, int]
    model: str


class EmbeddingService(ABC):
    """嵌入服务接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name", "")
        self.dimension = config.get("dimension", 1536)
        self.is_available = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入"""
        pass
    
    @abstractmethod
    async def embed_single_text(self, text: str) -> List[float]:
        """单个文本嵌入"""
        pass
    
    @abstractmethod
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        pass
    
    @abstractmethod
    async def find_similar_texts(
        self, 
        query_text: str, 
        candidate_texts: List[str], 
        top_k: int = 5
    ) -> List[tuple]:
        """查找相似文本"""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算欧几里得距离"""
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        return np.linalg.norm(vec1_array - vec2_array)
    
    async def close(self) -> None:
        """关闭服务连接"""
        pass
    
    def __str__(self) -> str:
        return f"EmbeddingService({self.model_name}, dim={self.dimension})"