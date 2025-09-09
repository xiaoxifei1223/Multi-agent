# 基于 Python Semantic Kernel 的多智能体系统

## 项目概述

本项目是一个功能完整的多智能体系统，基于 Python Semantic Kernel 框架构建，支持 Azure OpenAI 和阿里千问两种主流大语言模型。系统实现了9种常见的多智能体协作范式，提供了灵活、可扩展的智能体开发框架。

## 核心特性

### 🤖 支持的模型服务
- **Azure OpenAI**: GPT-4, GPT-3.5-turbo, text-embedding-ada-002
- **阿里千问**: qwen-max, qwen-plus, text-embedding-v1

### 🎯 九种智能体范式

1. **Reflection（反思模式）**
   - 智能体能够反思和改进自己的输出
   - 支持多轮反思优化
   - 提供质量评估机制
   - 支持跨智能体反思

2. **Tool Use（工具使用模式）**
   - 智能体可以调用外部工具和API
   - 可扩展的工具注册系统
   - 支持动态工具发现和调用

3. **Planning（规划模式）**
   - 智能体可以制定和执行复杂计划
   - 分层任务分解
   - 动态计划调整

4. **Multi-agent Collaboration（多智能体协作）**
   - 多个智能体协同工作
   - 消息传递和协调机制
   - 角色分工和任务分配

5. **Sequential Execution（顺序执行）**
   - 智能体按顺序处理任务流
   - 流水线式处理
   - 状态传递机制

6. **Parallel Execution（并行执行）**
   - 智能体并行处理任务
   - 负载均衡和任务分发
   - 结果汇聚机制

7. **Hierarchical（层次化）**
   - 具有上下级关系的智能体结构
   - 监督者和工作者模式
   - 层次化决策机制

8. **Democracy（民主模式）**
   - 智能体通过投票或协商做决策
   - 共识达成机制
   - 多数决定原则

9. **Competitive（竞争模式）**
   - 智能体之间竞争产生最佳结果
   - 方案比较和评选
   - 性能驱动的优化

## 系统架构

### 核心模块 (core/)

#### 基础类 (base/)
- **agent.py**: 智能体基类，定义通用接口
- **pattern.py**: 范式基类，定义协作模式
- **message.py**: 消息系统，处理智能体间通信

#### 服务层 (services/)
- **llm_service.py**: LLM服务接口定义
- **embedding_service.py**: 嵌入服务接口定义
- **azure_service.py**: Azure OpenAI 服务实现
- **qwen_service.py**: 阿里千问服务实现

#### 记忆系统 (memory/)
- **memory_store.py**: 记忆存储管理，支持多种记忆类型
- **vector_store.py**: 向量存储，支持 Faiss 和 ChromaDB

### 配置模块 (config/)
- **settings.py**: 全局配置管理
- **azure_config.py**: Azure OpenAI 配置
- **qwen_config.py**: 千问模型配置

### 范式实现 (patterns/)
每种范式都有独立的模块实现：
- **reflection/**: 反思模式实现
- **tool_use/**: 工具使用模式实现
- **planning/**: 规划模式实现
- **collaboration/**: 多智能体协作实现
- **sequential/**: 顺序执行实现
- **parallel/**: 并行执行实现
- **hierarchical/**: 层次化实现
- **democracy/**: 民主模式实现
- **competitive/**: 竞争模式实现

## 关键特性详解

### 🧠 智能记忆系统
- **多层级记忆**: 短期、长期、工作、情景、语义、程序记忆
- **重要性评级**: 自动评估和管理记忆重要性
- **过期机制**: 自动清理过期和低价值记忆
- **向量检索**: 基于语义相似度的快速检索

### 🔧 灵活的工具系统
- **动态注册**: 运行时动态注册和发现工具
- **类型安全**: 强类型工具接口定义
- **权限控制**: 基于角色的工具访问控制
- **批量执行**: 支持批量工具调用优化

### 📡 高效的消息系统
- **异步通信**: 基于 asyncio 的高性能消息传递
- **优先级队列**: 支持消息优先级和队列管理
- **广播机制**: 支持一对多的消息广播
- **消息持久化**: 可选的消息历史存储

### 🔄 智能协调机制
- **角色分工**: 明确的智能体角色定义和分工
- **状态同步**: 实时的智能体状态监控和同步
- **冲突解决**: 内置的冲突检测和解决机制
- **负载均衡**: 智能的任务分配和负载均衡

## 使用示例

### 基础使用
```python
import asyncio
from core.services.azure_service import AzureLLMService
from patterns.reflection.reflection_pattern import ReflectionPattern, ReflectionPatternConfig

async def main():
    # 初始化服务
    llm_service = AzureLLMService()
    await llm_service.initialize()
    
    # 创建反思范式
    config = ReflectionPatternConfig(
        name="智能助手",
        max_reflection_rounds=3,
        reflection_threshold=0.8
    )
    pattern = ReflectionPattern(config, llm_service)
    
    # 创建智能体
    agent = pattern.create_reflection_agent("深度思考者")
    
    # 执行任务
    result = await pattern.execute("请解释人工智能的发展趋势")
    print(result)

asyncio.run(main())
```

### 多模式协作
```python
# 组合多种范式
from patterns.planning.planning_pattern import PlanningPattern
from patterns.collaboration.collaboration_pattern import CollaborationPattern

# 创建规划智能体
planning_pattern = PlanningPattern(planning_config, llm_service)
planner = planning_pattern.create_planning_agent("规划师")

# 创建协作智能体
collab_pattern = CollaborationPattern(collab_config, llm_service)
executor1 = collab_pattern.create_worker_agent("执行者1")
executor2 = collab_pattern.create_worker_agent("执行者2")

# 协调执行
plan = await planner.create_plan("开发一个Web应用")
results = await collab_pattern.execute_plan(plan, [executor1, executor2])
```

## 配置说明

### 环境变量配置
```bash
# Azure OpenAI 配置
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# 阿里千问配置
DASHSCOPE_API_KEY=your_dashscope_api_key
QWEN_MODEL_NAME=qwen-max

# 系统配置
LOG_LEVEL=INFO
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./data/vector_store
```

### 智能体配置
```python
# 反思智能体配置
ReflectionPatternConfig(
    max_reflection_rounds=3,      # 最大反思轮次
    reflection_threshold=0.8,     # 质量阈值
    enable_cross_agent_reflection=True  # 启用跨智能体反思
)

# 工具使用配置
ToolUsePatternConfig(
    allowed_tools=["web_search", "calculator"],  # 允许的工具
    tool_timeout=30,              # 工具调用超时
    parallel_tool_calls=True      # 并行工具调用
)
```

## 性能优化

### 🚀 异步处理
- 全异步架构，支持高并发
- 非阻塞的消息传递和工具调用
- 批量操作优化

### 💾 内存管理
- 智能的记忆清理机制
- 向量索引优化
- 缓存策略优化

### 🔄 负载均衡
- 智能的任务分配
- 动态的智能体调度
- 资源使用监控

## 测试和质量保证

### 🧪 测试覆盖
- 单元测试: 核心组件和算法测试
- 集成测试: 服务集成和模式测试
- 端到端测试: 完整工作流测试

### 📊 性能监控
- 响应时间监控
- 资源使用统计
- 错误率跟踪

### 🔍 调试工具
- 详细的日志系统
- 智能体状态可视化
- 消息流跟踪

## 扩展性

### 🔌 插件架构
- 可插拔的模式实现
- 自定义工具开发接口
- 第三方服务集成

### 🎨 自定义开发
- 继承基类实现自定义智能体
- 实现自定义范式
- 添加新的服务提供商

### 📈 横向扩展
- 分布式智能体部署
- 微服务架构支持
- 容器化部署

## 部署和运维

### 🐳 容器化部署
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "examples.basic_usage.simple_chat"]
```

### ☁️ 云部署
- 支持 Azure Container Instances
- AWS ECS/Fargate 部署
- 阿里云容器服务

### 📊 监控告警
- Prometheus 指标采集
- Grafana 可视化面板
- 告警规则配置

## 社区和支持

### 📚 文档资源
- 详细的API文档
- 范式使用指南
- 最佳实践案例

### 🤝 社区贡献
- GitHub Issues 问题反馈
- Pull Request 代码贡献
- 社区讨论和分享

### 🔄 版本更新
- 定期功能更新
- 安全补丁发布
- 兼容性维护

---

## 快速开始

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/multi-agent-sk.git
   cd multi-agent-sk
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API 密钥
   ```

4. **运行示例**
   ```bash
   python examples/patterns_demo/reflection_demo.py
   ```

5. **开始开发**
   ```python
   # 查看更多示例
   python examples/basic_usage/simple_chat.py
   python examples/advanced/multi_model_usage.py
   ```

通过这个项目，你可以快速构建功能强大的多智能体应用，充分发挥大语言模型在协作和推理方面的优势！