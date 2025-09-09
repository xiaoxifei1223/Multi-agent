"""
基于 Semantic Kernel 的千问服务实现
注意：由于 Semantic Kernel 原生不支持千问，这里提供自定义实现
"""
import asyncio
from typing import Any, Dict, List, Optional
import dashscope
from dashscope.api_entities.dashscope_response import GenerationResponse

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.text_embedding_base import TextEmbeddingBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.kernel import Kernel

from ...config.qwen_config import get_qwen_config


class QwenChatCompletion(ChatCompletionClientBase):
    """
    千问聊天补全服务 - 实现 Semantic Kernel 接口
    """
    
    def __init__(self):
        self.config = get_qwen_config()
        self.model_name = self.config.model_name
        dashscope.api_key = self.config.api_key
    
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[ChatMessageContent]:
        """获取聊天消息内容"""
        try:
            # 转换聊天历史为千问格式
            messages = self._convert_chat_history(chat_history)
            
            # 调用千问API
            response = await asyncio.to_thread(
                dashscope.Generation.call,
                model=self.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                result_format='message'
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"千问API错误: {response.message}")
            
            # 转换响应为 Semantic Kernel 格式
            content = response.output.choices[0].message.content
            
            return [ChatMessageContent.create(
                role="assistant",
                content=content
            )]
            
        except Exception as e:
            raise RuntimeError(f"千问聊天补全失败: {e}")
    
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[StreamingChatMessageContent]:
        """获取流式聊天消息内容"""
        try:
            messages = self._convert_chat_history(chat_history)
            
            def _stream_generate():
                responses = dashscope.Generation.call(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    top_p=self.config.top_p,
                    result_format='message',
                    stream=True
                )
                
                for response in responses:
                    if response.status_code == 200:
                        yield response.output.choices[0].message.content
                    else:
                        raise RuntimeError(f"流式错误: {response.message}")
            
            # 转换为流式内容
            streaming_contents = []
            loop = asyncio.get_event_loop()
            
            generator = _stream_generate()
            while True:
                try:
                    chunk = await loop.run_in_executor(None, next, generator)
                    streaming_contents.append(
                        StreamingChatMessageContent(
                            role="assistant",
                            content=chunk
                        )
                    )
                except StopIteration:
                    break
            
            return streaming_contents
            
        except Exception as e:
            raise RuntimeError(f"千问流式补全失败: {e}")
    
    def _convert_chat_history(self, chat_history: ChatHistory) -> List[Dict[str, str]]:
        """转换聊天历史为千问格式"""
        messages = []
        
        for message in chat_history.messages:
            role = message.role
            if role not in ["user", "assistant", "system"]:
                role = "user"
            
            messages.append({
                "role": role,
                "content": str(message.content)
            })
        
        return messages


class QwenTextEmbedding(TextEmbeddingBase):
    """
    千问文本嵌入服务 - 实现 Semantic Kernel 接口
    """
    
    def __init__(self):
        self.config = get_qwen_config()
        self.model_name = self.config.embedding_model
        dashscope.api_key = self.config.api_key
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本嵌入"""
        try:
            response = await asyncio.to_thread(
                dashscope.TextEmbedding.call,
                model=self.model_name,
                input=texts
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"千问嵌入API错误: {response.message}")
            
            return [data['embedding'] for data in response.output['embeddings']]
            
        except Exception as e:
            raise RuntimeError(f"千问嵌入生成失败: {e}")


class SKQwenServiceManager:
    """
    基于 Semantic Kernel 的千问服务管理器
    """
    
    def __init__(self):
        self.config = get_qwen_config()
        self.chat_service: Optional[QwenChatCompletion] = None
        self.embedding_service: Optional[QwenTextEmbedding] = None
        self.kernel: Optional[Kernel] = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """初始化千问服务"""
        try:
            # 初始化千问服务
            self.chat_service = QwenChatCompletion()
            self.embedding_service = QwenTextEmbedding()
            
            # 初始化 Kernel
            self.kernel = Kernel()
            self.kernel.add_service(self.chat_service)
            self.kernel.add_service(self.embedding_service)
            
            self.is_initialized = True
            print(f"✅ 千问服务初始化成功")
            
        except Exception as e:
            print(f"❌ 千问服务初始化失败: {e}")
            self.is_initialized = False
            raise
    
    def get_chat_service(self) -> QwenChatCompletion:
        """获取聊天服务"""
        if not self.is_initialized or self.chat_service is None:
            raise RuntimeError("服务未初始化")
        return self.chat_service
    
    def get_embedding_service(self) -> QwenTextEmbedding:
        """获取嵌入服务"""
        if not self.is_initialized or self.embedding_service is None:
            raise RuntimeError("服务未初始化")
        return self.embedding_service
    
    def get_kernel(self) -> Kernel:
        """获取 Kernel"""
        if not self.is_initialized or self.kernel is None:
            raise RuntimeError("服务未初始化")
        return self.kernel
    
    async def check_health(self) -> bool:
        """健康检查"""
        try:
            if not self.is_initialized or self.chat_service is None:
                return False
            
            # 简单的健康检查
            return True
            
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": "Alibaba Qwen (Semantic Kernel)",
            "chat_model": self.config.model_name,
            "embedding_model": self.config.embedding_model,
            "api_key": self.config.api_key[:10] + "...",
            "is_initialized": self.is_initialized,
            "kernel_services": len(self.kernel.services) if self.kernel else 0
        }
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本嵌入"""
        if not self.is_initialized or self.embedding_service is None:
            raise RuntimeError("嵌入服务未初始化")
        
        try:
            return await self.embedding_service.generate_embeddings(texts)
            
        except Exception as e:
            print(f"获取嵌入失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭服务连接"""
        self.is_initialized = False
        print("千问服务连接已关闭")


# 全局服务管理器实例
_qwen_service_manager: Optional[SKQwenServiceManager] = None


async def get_qwen_service_manager() -> SKQwenServiceManager:
    """获取全局千问服务管理器"""
    global _qwen_service_manager
    
    if _qwen_service_manager is None:
        _qwen_service_manager = SKQwenServiceManager()
        await _qwen_service_manager.initialize()
    
    return _qwen_service_manager


async def create_qwen_chat_agent(
    name: str,
    instructions: str,
    kernel: Optional[Kernel] = None
) -> 'ChatCompletionAgent':
    """创建千问聊天智能体"""
    from semantic_kernel.agents import ChatCompletionAgent
    
    service_manager = await get_qwen_service_manager()
    
    if kernel is None:
        kernel = service_manager.get_kernel()
    
    agent = ChatCompletionAgent(
        service=service_manager.get_chat_service(),
        name=name,
        instructions=instructions,
        kernel=kernel
    )
    
    return agent