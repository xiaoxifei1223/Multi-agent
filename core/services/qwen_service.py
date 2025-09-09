"""
阿里千问服务实现
"""
import asyncio
from typing import Any, Dict, List, Optional, AsyncIterator
import dashscope
from dashscope.api_entities.dashscope_response import GenerationResponse
import json
import time

from ..services.llm_service import LLMService, LLMRequest, LLMResponse
from ..services.embedding_service import EmbeddingService, EmbeddingRequest, EmbeddingResponse
from ...config.qwen_config import get_qwen_config


class QwenLLMService(LLMService):
    """阿里千问 LLM 服务实现"""
    
    def __init__(self):
        config = get_qwen_config()
        super().__init__(config.dict())
        self.model_name = config.model_name
        
    async def initialize(self) -> None:
        """初始化千问服务"""
        try:
            dashscope.api_key = self.config["api_key"]
            self.is_available = await self.check_health()
        except Exception as e:
            print(f"Failed to initialize Qwen service: {e}")
            self.is_available = False
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """聊天补全"""
        try:
            # 转换消息格式
            messages = self._convert_messages(request.messages)
            
            response = await asyncio.to_thread(
                dashscope.Generation.call,
                model=self.model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                repetition_penalty=self.config.get("repetition_penalty", 1.0),
                result_format='message'
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Qwen API error: {response.message}")
            
            output = response.output
            return LLMResponse(
                content=output.choices[0].message.content,
                usage=response.usage,
                finish_reason=output.choices[0].finish_reason,
                model=self.model_name,
                created=int(time.time())
            )
        except Exception as e:
            raise RuntimeError(f"Chat completion failed: {e}")
    
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """流式聊天补全"""
        try:
            messages = self._convert_messages(request.messages)
            
            def _stream_generate():
                responses = dashscope.Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    repetition_penalty=self.config.get("repetition_penalty", 1.0),
                    result_format='message',
                    stream=True
                )
                
                for response in responses:
                    if response.status_code == 200:
                        yield response.output.choices[0].message.content
                    else:
                        raise RuntimeError(f"Stream error: {response.message}")
            
            # 在线程池中运行生成器
            loop = asyncio.get_event_loop()
            
            def sync_generator():
                for chunk in _stream_generate():
                    yield chunk
            
            generator = sync_generator()
            while True:
                try:
                    chunk = await loop.run_in_executor(None, next, generator)
                    yield chunk
                except StopIteration:
                    break
                    
        except Exception as e:
            raise RuntimeError(f"Stream completion failed: {e}")
    
    async def function_call(self, request: LLMRequest) -> LLMResponse:
        """函数调用 - 千问支持插件调用"""
        # 千问的工具调用实现
        return await self.chat_completion(request)
    
    async def check_health(self) -> bool:
        """健康检查"""
        try:
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
            "provider": "Alibaba Qwen",
            "model_name": self.model_name,
            "api_key": self.config.get("api_key", "")[:10] + "...",
            "is_available": self.is_available
        }
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """转换消息格式以符合千问API要求"""
        converted_messages = []
        for msg in messages:
            # 千问支持的角色: user, assistant, system
            role = msg.get("role", "user")
            if role not in ["user", "assistant", "system"]:
                role = "user"
            
            converted_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })
        
        return converted_messages


class QwenEmbeddingService(EmbeddingService):
    """阿里千问嵌入服务实现"""
    
    def __init__(self):
        config = get_qwen_config()
        super().__init__({
            "model_name": config.embedding_model,
            "dimension": 1536,  # text-embedding-v1 的维度
            **config.dict()
        })
        
    async def initialize(self) -> None:
        """初始化千问嵌入服务"""
        try:
            dashscope.api_key = self.config["api_key"]
            self.is_available = await self.check_health()
        except Exception as e:
            print(f"Failed to initialize Qwen embedding service: {e}")
            self.is_available = False
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入"""
        try:
            response = await asyncio.to_thread(
                dashscope.TextEmbedding.call,
                model=self.config["embedding_model"],
                input=texts
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Qwen embedding API error: {response.message}")
            
            return [data['embedding'] for data in response.output['embeddings']]
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
        try:
            await self.embed_single_text("test")
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "Alibaba Qwen",
            "model_name": self.config["embedding_model"],
            "dimension": self.dimension,
            "api_key": self.config.get("api_key", "")[:10] + "...",
            "is_available": self.is_available
        }