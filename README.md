# Multi-Agent System Based on Semantic Kernel

基于 Python Semantic Kernel 的多智能体系统，支持 Azure OpenAI 和阿里千问模型。

## 项目概述

这是一个功能完整的多智能体系统，实现了9种常见的智能体协作范式：

### 支持的智能体范式

1. **Reflection（反思模式）** - 智能体能够反思和改进自己的输出
2. **Tool Use（工具使用模式）** - 智能体可以调用外部工具和API
3. **Planning（规划模式）** - 智能体可以制定和执行复杂计划
4. **Multi-agent Collaboration（多智能体协作）** - 多个智能体协同工作
5. **Sequential Execution（顺序执行）** - 智能体按顺序处理任务流
6. **Parallel Execution（并行执行）** - 智能体并行处理任务
7. **Hierarchical（层次化）** - 具有上下级关系的智能体结构
8. **Democracy（民主模式）** - 智能体通过投票或协商做决策
9. **Competitive（竞争模式）** - 智能体之间竞争产生最佳结果

### 支持的模型

- **Azure OpenAI**: GPT-4, GPT-3.5-turbo, text-embedding-ada-002
- **阿里千问**: qwen-max, qwen-plus, text-embedding-v1

## 项目结构

```
Multi-agent/
├── README.md                          # 项目说明文档
├── requirements.txt                   # 项目依赖
├── pyproject.toml                     # 项目配置
├── .env.example                       # 环境变量示例
├── config/                            # 配置文件
│   ├── __init__.py
│   ├── settings.py                    # 全局配置
│   ├── azure_config.py               # Azure OpenAI 配置
│   └── qwen_config.py                # 千问模型配置
├── core/                              # 核心模块
│   ├── __init__.py
│   ├── base/                          # 基础类定义
│   │   ├── __init__.py
│   │   ├── agent.py                   # 智能体基类
│   │   ├── pattern.py                 # 范式基类
│   │   └── message.py                 # 消息系统
│   ├── services/                      # 服务层
│   │   ├── __init__.py
│   │   ├── llm_service.py            # LLM服务接口
│   │   ├── embedding_service.py       # 嵌入服务接口
│   │   ├── azure_service.py          # Azure OpenAI 服务实现
│   │   └── qwen_service.py           # 千问服务实现
│   └── memory/                        # 记忆系统
│       ├── __init__.py
│       ├── memory_store.py           # 记忆存储
│       └── vector_store.py           # 向量存储
├── patterns/                          # 9种智能体范式实现
│   ├── __init__.py
│   ├── reflection/                    # 反思模式
│   │   ├── __init__.py
│   │   ├── reflection_agent.py
│   │   └── reflection_pattern.py
│   ├── tool_use/                      # 工具使用模式
│   │   ├── __init__.py
│   │   ├── tool_agent.py
│   │   ├── tool_registry.py
│   │   └── tools/                     # 具体工具实现
│   │       ├── __init__.py
│   │       ├── web_search.py
│   │       ├── calculator.py
│   │       └── file_operations.py
│   ├── planning/                      # 规划模式
│   │   ├── __init__.py
│   │   ├── planning_agent.py
│   │   ├── task_planner.py
│   │   └── execution_engine.py
│   ├── collaboration/                 # 多智能体协作
│   │   ├── __init__.py
│   │   ├── collaboration_manager.py
│   │   └── coordinator_agent.py
│   ├── sequential/                    # 顺序执行
│   │   ├── __init__.py
│   │   ├── sequential_agent.py
│   │   └── workflow_manager.py
│   ├── parallel/                      # 并行执行
│   │   ├── __init__.py
│   │   ├── parallel_agent.py
│   │   └── task_distributor.py
│   ├── hierarchical/                  # 层次化
│   │   ├── __init__.py
│   │   ├── supervisor_agent.py
│   │   └── worker_agent.py
│   ├── democracy/                     # 民主模式
│   │   ├── __init__.py
│   │   ├── voting_agent.py
│   │   └── consensus_manager.py
│   └── competitive/                   # 竞争模式
│       ├── __init__.py
│       ├── competitive_agent.py
│       └── competition_manager.py
├── examples/                          # 示例代码
│   ├── __init__.py
│   ├── basic_usage/                   # 基础使用示例
│   │   ├── simple_chat.py
│   │   ├── tool_usage.py
│   │   └── planning_example.py
│   ├── patterns_demo/                 # 各种范式演示
│   │   ├── reflection_demo.py
│   │   ├── collaboration_demo.py
│   │   ├── hierarchical_demo.py
│   │   └── democracy_demo.py
│   └── advanced/                      # 高级用法示例
│       ├── multi_model_usage.py
│       ├── custom_tools.py
│       └── complex_workflow.py
├── tests/                             # 测试代码
│   ├── __init__.py
│   ├── unit/                          # 单元测试
│   │   ├── test_agents.py
│   │   ├── test_services.py
│   │   └── test_patterns.py
│   ├── integration/                   # 集成测试
│   │   ├── test_azure_integration.py
│   │   └── test_qwen_integration.py
│   └── e2e/                          # 端到端测试
│       └── test_workflows.py
├── docs/                              # 文档
│   ├── api/                          # API文档
│   ├── patterns/                     # 范式详细说明
│   ├── examples/                     # 示例文档
│   └── deployment/                   # 部署指南
└── scripts/                          # 脚本工具
    ├── setup.py                      # 安装脚本
    ├── run_examples.py              # 运行示例脚本
    └── benchmark.py                 # 性能基准测试
```

## 快速开始

1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量：复制 `.env.example` 为 `.env` 并填入相关配置
4. 运行示例：`python examples/basic_usage/simple_chat.py`

## 特性

- 🤖 支持多种智能体范式
- 🔧 可扩展的工具系统
- 💾 灵活的记忆管理
- 🔄 支持多模型切换
- 📊 完整的监控和日志
- 🧪 全面的测试覆盖

## 许可证

MIT License