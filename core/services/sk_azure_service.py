"""
基于 Semantic Kernel 的 Azure OpenAI 服务实现
"""
import asyncio
from typing import Any, Dict, List, Optional

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.kernel import Kernel

from ...config.azure_config import get_azure_config


class SKAzureServiceManager:
    """
    基于 Semantic Kernel 的 Azure OpenAI 服务管理器
    """
    
    def __init__(self):
        self.config = get_azure_config()
        self.chat_service: Optional[AzureChatCompletion] = None
        self.embedding_service: Optional[AzureTextEmbedding] = None
        self.kernel: Optional[Kernel] = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """初始化 Azure OpenAI 服务"""
        try:
            # 初始化 Azure Chat Completion 服务
            self.chat_service = AzureChatCompletion(
                deployment_name=self.config.deployment_name,
                endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version
            )
            
            # 初始化 Azure Text Embedding 服务
            self.embedding_service = AzureTextEmbedding(
                deployment_name=self.config.embedding_deployment,
                endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version
            )
            
            # 初始化 Kernel
            self.kernel = Kernel()
            self.kernel.add_service(self.chat_service)
            self.kernel.add_service(self.embedding_service)
            
            self.is_initialized = True
            print(f"✅ Azure OpenAI 服务初始化成功")
            
        except Exception as e:
            print(f"❌ Azure OpenAI 服务初始化失败: {e}")
            self.is_initialized = False
            raise
    
    def get_chat_service(self) -> AzureChatCompletion:
        """获取聊天服务"""
        if not self.is_initialized or self.chat_service is None:
            raise RuntimeError("服务未初始化")
        return self.chat_service
    
    def get_embedding_service(self) -> AzureTextEmbedding:
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
            
            # 简单的健康检查 - 实际项目中可以调用API测试
            return True
            
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": "Azure OpenAI (Semantic Kernel)",
            "chat_model": self.config.deployment_name,
            "embedding_model": self.config.embedding_deployment,
            "endpoint": self.config.endpoint,
            "api_version": self.config.api_version,
            "is_initialized": self.is_initialized,
            "kernel_services": len(self.kernel.services) if self.kernel else 0
        }
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本嵌入"""
        if not self.is_initialized or self.embedding_service is None:
            raise RuntimeError("嵌入服务未初始化")
        
        try:
            # 使用 Semantic Kernel 的嵌入服务
            embeddings = []
            for text in texts:
                result = await self.embedding_service.generate_embeddings([text])
                if result and len(result) > 0:
                    embeddings.append(result[0])
                else:
                    embeddings.append([])
            
            return embeddings
            
        except Exception as e:
            print(f"获取嵌入失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭服务连接"""
        # Semantic Kernel 的服务通常不需要显式关闭
        self.is_initialized = False
        print("Azure OpenAI 服务连接已关闭")


# 全局服务管理器实例
_azure_service_manager: Optional[SKAzureServiceManager] = None


async def get_azure_service_manager() -> SKAzureServiceManager:
    """获取全局 Azure 服务管理器"""
    global _azure_service_manager
    
    if _azure_service_manager is None:
        _azure_service_manager = SKAzureServiceManager()
        await _azure_service_manager.initialize()
    
    return _azure_service_manager


async def create_azure_chat_agent(
    name: str,
    instructions: str,
    kernel: Optional[Kernel] = None
) -> 'ChatCompletionAgent':
    """创建 Azure 聊天智能体"""
    from semantic_kernel.agents import ChatCompletionAgent
    
    service_manager = await get_azure_service_manager()
    
    if kernel is None:
        kernel = service_manager.get_kernel()
    
    agent = ChatCompletionAgent(
        service=service_manager.get_chat_service(),
        name=name,
        instructions=instructions,
        kernel=kernel
    )
    
    return agent