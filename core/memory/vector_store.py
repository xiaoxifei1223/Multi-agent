"""
向量存储系统
"""
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import numpy as np
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorDocument(BaseModel):
    """向量文档"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """搜索结果"""
    
    document: VectorDocument
    score: float
    rank: int


class VectorStore(ABC):
    """向量存储基类"""
    
    def __init__(self, dimension: int, config: Dict[str, Any] = None):
        self.dimension = dimension
        self.config = config or {}
        self.documents: Dict[str, VectorDocument] = {}
    
    @abstractmethod
    async def add_document(self, document: VectorDocument) -> str:
        """添加文档"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """批量添加文档"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, document: VectorDocument) -> bool:
        """更新文档"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        pass
    
    async def search_by_text(
        self, 
        query_text: str, 
        embedding_service,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """通过文本搜索"""
        query_vector = await embedding_service.embed_single_text(query_text)
        return await self.search(query_vector, top_k, filter_metadata)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "config": self.config
        }


class FaissVectorStore(VectorStore):
    """基于 Faiss 的向量存储"""
    
    def __init__(self, dimension: int, config: Dict[str, Any] = None):
        if not FAISS_AVAILABLE:
            raise ImportError("Faiss not available. Install with: pip install faiss-cpu")
        
        super().__init__(dimension, config)
        
        # 创建 Faiss 索引
        index_type = config.get("index_type", "flat") if config else "flat"
        if index_type == "flat":
            self.index = faiss.IndexFlatIP(dimension)  # 内积索引
        elif index_type == "ivf":
            nlist = config.get("nlist", 100)
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")
        
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.next_index = 0
        
    async def add_document(self, document: VectorDocument) -> str:
        """添加文档"""
        # 归一化向量（用于余弦相似度）
        vector = np.array(document.vector, dtype=np.float32)
        vector = vector / np.linalg.norm(vector)
        
        # 添加到 Faiss 索引
        self.index.add(vector.reshape(1, -1))
        
        # 存储映射关系
        self.id_to_index[document.id] = self.next_index
        self.index_to_id[self.next_index] = document.id
        self.next_index += 1
        
        # 存储文档
        self.documents[document.id] = document
        
        return document.id
    
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """批量添加文档"""
        if not documents:
            return []
        
        # 准备向量
        vectors = []
        for doc in documents:
            vector = np.array(doc.vector, dtype=np.float32)
            vector = vector / np.linalg.norm(vector)
            vectors.append(vector)
        
        vectors_array = np.vstack(vectors)
        
        # 批量添加到索引
        self.index.add(vectors_array)
        
        # 更新映射关系和存储文档
        doc_ids = []
        for doc in documents:
            self.id_to_index[doc.id] = self.next_index
            self.index_to_id[self.next_index] = doc.id
            self.next_index += 1
            
            self.documents[doc.id] = doc
            doc_ids.append(doc.id)
        
        return doc_ids
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        if self.index.ntotal == 0:
            return []
        
        # 归一化查询向量
        query = np.array(query_vector, dtype=np.float32)
        query = query / np.linalg.norm(query)
        query = query.reshape(1, -1)
        
        # 搜索
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # Faiss 返回 -1 表示无效结果
                continue
            
            doc_id = self.index_to_id.get(idx)
            if doc_id and doc_id in self.documents:
                document = self.documents[doc_id]
                
                # 应用元数据过滤
                if filter_metadata:
                    if not self._match_metadata_filter(document.metadata, filter_metadata):
                        continue
                
                results.append(SearchResult(
                    document=document,
                    score=float(score),
                    rank=rank
                ))
        
        return results
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        if document_id not in self.documents:
            return False
        
        # 从 Faiss 索引中删除比较复杂，这里标记为删除
        # 实际应用中可能需要重建索引
        del self.documents[document_id]
        
        if document_id in self.id_to_index:
            idx = self.id_to_index[document_id]
            del self.id_to_index[document_id]
            if idx in self.index_to_id:
                del self.index_to_id[idx]
        
        return True
    
    async def update_document(self, document_id: str, document: VectorDocument) -> bool:
        """更新文档"""
        if document_id not in self.documents:
            return False
        
        # 删除旧文档并添加新文档
        await self.delete_document(document_id)
        await self.add_document(document)
        return True
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        return self.documents.get(document_id)
    
    def _match_metadata_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


class ChromaVectorStore(VectorStore):
    """基于 ChromaDB 的向量存储"""
    
    def __init__(self, dimension: int, config: Dict[str, Any] = None):
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
        
        super().__init__(dimension, config)
        
        # 初始化 ChromaDB
        self.client = chromadb.Client()
        collection_name = config.get("collection_name", "default") if config else "default"
        
        try:
            self.collection = self.client.get_collection(collection_name)
        except ValueError:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"dimension": dimension}
            )
    
    async def add_document(self, document: VectorDocument) -> str:
        """添加文档"""
        self.collection.add(
            ids=[document.id],
            embeddings=[document.vector],
            documents=[document.content],
            metadatas=[document.metadata]
        )
        
        self.documents[document.id] = document
        return document.id
    
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """批量添加文档"""
        if not documents:
            return []
        
        ids = [doc.id for doc in documents]
        embeddings = [doc.vector for doc in documents]
        docs = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=docs,
            metadatas=metadatas
        )
        
        for doc in documents:
            self.documents[doc.id] = doc
        
        return ids
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        # 构建 where 条件
        where_condition = filter_metadata if filter_metadata else None
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_condition
        )
        
        search_results = []
        if results["ids"] and results["ids"][0]:
            for rank, (doc_id, distance) in enumerate(zip(results["ids"][0], results["distances"][0])):
                if doc_id in self.documents:
                    document = self.documents[doc_id]
                    # ChromaDB 返回距离，转换为相似度分数
                    score = 1.0 / (1.0 + distance)
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=score,
                        rank=rank
                    ))
        
        return search_results
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        if document_id not in self.documents:
            return False
        
        try:
            self.collection.delete(ids=[document_id])
            del self.documents[document_id]
            return True
        except Exception:
            return False
    
    async def update_document(self, document_id: str, document: VectorDocument) -> bool:
        """更新文档"""
        if document_id not in self.documents:
            return False
        
        try:
            self.collection.update(
                ids=[document.id],
                embeddings=[document.vector],
                documents=[document.content],
                metadatas=[document.metadata]
            )
            self.documents[document.id] = document
            return True
        except Exception:
            return False
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        return self.documents.get(document_id)


def create_vector_store(
    store_type: str, 
    dimension: int, 
    config: Dict[str, Any] = None
) -> VectorStore:
    """创建向量存储实例"""
    if store_type.lower() == "faiss":
        return FaissVectorStore(dimension, config)
    elif store_type.lower() == "chroma":
        return ChromaVectorStore(dimension, config)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")