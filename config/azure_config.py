"""
Azure OpenAI 配置
"""
from typing import Optional
from pydantic import BaseSettings, Field


class AzureOpenAIConfig(BaseSettings):
    """Azure OpenAI 配置类"""
    
    api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    api_version: str = Field(default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    deployment_name: str = Field(..., env="AZURE_OPENAI_DEPLOYMENT_NAME")
    embedding_deployment: str = Field(..., env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    
    # 模型参数
    temperature: float = Field(default=0.7, description="模型创造性参数")
    max_tokens: int = Field(default=4000, description="最大生成token数")
    top_p: float = Field(default=0.9, description="核采样参数")
    frequency_penalty: float = Field(default=0.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, description="存在惩罚")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_azure_config() -> AzureOpenAIConfig:
    """获取Azure OpenAI配置"""
    return AzureOpenAIConfig()