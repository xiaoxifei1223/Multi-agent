"""
Azure OpenAI 服务实现 - 基于 Semantic Kernel
"""
import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.kernel import Kernel
from semantic_kernel import Kernel

from ...config.azure_config import get_azure_config


class AzureLLMService(LLMService):
    """Azure OpenAI LLM 服务实现"""
    
    def __init__(self):
        config = get_azure_config()
        super().__init__(config.dict())
        self.client: Optional[AsyncAzureOpenAI] = None
        self.deployment_name = config.deployment_name
        
    async def initialize(self) -> None:
        """初始化 Azure OpenAI 客户端"""
        try:
            self.client = AsyncAzureOpenAI(
                api_key=self.config["api_key"],
                api_version=self.config["api_version"],
                azure_endpoint=self.config["endpoint"]
            )
            self.is_available = await self.check_health()
        except Exception as e:
            print(f"Failed to initialize Azure OpenAI client: {e}")
            self.is_available = False
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """聊天补全"""
        if not self.client:
            raise RuntimeError("Service not initialized")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                functions=request.functions,
                function_call=request.function_call
            )
            
            choice = response.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                usage=response.usage.dict(),
                finish_reason=choice.finish_reason,
                function_call=choice.message.function_call.dict() if choice.message.function_call else None,
                model=response.model,
                created=response.created
            )
        except Exception as e:
            raise RuntimeError(f"Chat completion failed: {e}")
    
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """流式聊天补全"""
        if not self.client:
            raise RuntimeError("Service not initialized")
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"Stream completion failed: {e}")
    
    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """函数调用"""
        return await self.chat_completion(request)
    
    async def check_health(self) -> bool:
        """健康检查"""
        if not self.client:
            return False
        
        try:
            # 发送简单的健康检查请求
            test_request = LLMRequest(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            await self.chat_completion(test_request)
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "Azure OpenAI",
            "model_name": self.deployment_name,
            "endpoint": self.config.get("endpoint", ""),
            "api_version": self.config.get("api_version", ""),
            "is_available": self.is_available
        }


class AzureEmbeddingService(EmbeddingService):
    """Azure OpenAI 嵌入服务实现"""
    
    def __init__(self):
        config = get_azure_config()
        super().__init__({
            "model_name": config.embedding_deployment,
            "dimension": 1536,  # text-embedding-ada-002 的维度
            **config.dict()
        })
        self.client: Optional[AsyncAzureOpenAI] = None
        self.deployment_name = config.embedding_deployment
        
    async def initialize(self) -> None:
        """初始化 Azure OpenAI 客户端"""
        try:
            self.client = AsyncAzureOpenAI(
                api_key=self.config["api_key"],
                api_version=self.config["api_version"],
                azure_endpoint=self.config["endpoint"]
            )
            self.is_available = await self.check_health()
        except Exception as e:
            print(f"Failed to initialize Azure OpenAI embedding client: {e}")
            self.is_available = False
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入"""
        if not self.client:
            raise RuntimeError("Service not initialized")
        
        try:
            response = await self.client.embeddings.create(
                model=self.deployment_name,
                input=texts
            )
            
            return [data.embedding for data in response.data]
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}")
    
    async def embed_single_text(self, text: str) -> List[float]:
        """单个文本嵌入"""
        embeddings = await self.embed_texts([text])
        return embeddings[0]
    
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        embeddings = await self.embed_texts([text1, text2])
        return self.cosine_similarity(embeddings[0], embeddings[1])
    
    async def find_similar_texts(
        self, 
        query_text: str, 
        candidate_texts: List[str], 
        top_k: int = 5
    ) -> List[tuple]:
        """查找相似文本"""
        query_embedding = await self.embed_single_text(query_text)
        candidate_embeddings = await self.embed_texts(candidate_texts)
        
        similarities = []
        for i, candidate_embedding in enumerate(candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate_embedding)
            similarities.append((i, candidate_texts[i], similarity))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[2], reverse=True)
        return similarities[:top_k]
    
    async def check_health(self) -> bool:
        """健康检查"""
        if not self.client:
            return False
        
        try:
            # 发送简单的健康检查请求
            await self.embed_single_text("test")
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "Azure OpenAI",
            "model_name": self.deployment_name,
            "dimension": self.dimension,
            "endpoint": self.config.get("endpoint", ""),
            "api_version": self.config.get("api_version", ""),
            "is_available": self.is_available
        }