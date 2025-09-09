"""
阿里千问模型配置
"""
from typing import Optional
from pydantic import BaseSettings, Field


class QwenConfig(BaseSettings):
    """千问模型配置类"""
    
    api_key: str = Field(..., env="DASHSCOPE_API_KEY")
    model_name: str = Field(default="qwen-max", env="QWEN_MODEL_NAME")
    embedding_model: str = Field(default="text-embedding-v1", env="QWEN_EMBEDDING_MODEL")
    
    # 模型参数
    temperature: float = Field(default=0.7, description="模型创造性参数")
    max_tokens: int = Field(default=4000, description="最大生成token数")
    top_p: float = Field(default=0.9, description="核采样参数")
    top_k: int = Field(default=50, description="top-k采样参数")
    repetition_penalty: float = Field(default=1.0, description="重复惩罚")
    
    # API配置
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_qwen_config() -> QwenConfig:
    """获取千问配置"""
    return QwenConfig()