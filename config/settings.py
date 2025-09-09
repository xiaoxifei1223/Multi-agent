"""
全局配置管理
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class GlobalSettings(BaseSettings):
    """全局配置类"""
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 网络配置
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # 向量数据库配置
    vector_db_type: str = Field(default="faiss", env="VECTOR_DB_TYPE")
    vector_db_path: str = Field(default="./data/vector_store", env="VECTOR_DB_PATH")
    
    # Redis配置 (可选)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # API配置
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = GlobalSettings()


def get_settings() -> GlobalSettings:
    """获取全局配置"""
    return settings