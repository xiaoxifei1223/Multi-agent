"""
基于 Semantic Kernel 的基础智能体演示
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from semantic_kernel.agents import ChatCompletionAgent
from core.services.sk_azure_service import get_azure_service_manager, create_azure_chat_agent
from core.services.sk_qwen_service import get_qwen_service_manager, create_qwen_chat_agent


async def demo_azure_agent():
    """演示 Azure OpenAI 智能体"""
    print("🤖 Azure OpenAI 智能体演示")
    print("=" * 40)
    
    try:
        # 获取 Azure 服务管理器
        service_manager = await get_azure_service_manager()
        print(f"✅ Azure 服务信息: {service_manager.get_service_info()}")
        
        # 创建智能体
        agent = await create_azure_chat_agent(
            name="Azure-Assistant",
            instructions="你是一个有帮助的AI助手，请用中文回答问题。"
        )
        
        print(f"✅ 创建智能体: {agent.name}")
        
        # 交互对话
        user_input = "请用一句话介绍什么是人工智能"
        print(f"\n用户: {user_input}")
        
        # 获取响应
        response = await agent.invoke(messages=user_input)
        print(f"助手: {response}")
        
    except Exception as e:
        print(f"❌ Azure 演示失败: {e}")


async def demo_qwen_agent():
    """演示千问智能体"""
    print("\n🤖 千问智能体演示")
    print("=" * 40)
    
    try:
        # 获取千问服务管理器
        service_manager = await get_qwen_service_manager()
        print(f"✅ 千问服务信息: {service_manager.get_service_info()}")
        
        # 创建智能体
        agent = await create_qwen_chat_agent(
            name="Qwen-Assistant",
            instructions="你是一个有帮助的AI助手，请用中文回答问题。"
        )
        
        print(f"✅ 创建智能体: {agent.name}")
        
        # 交互对话
        user_input = "请解释一下机器学习的基本概念"
        print(f"\n用户: {user_input}")
        
        # 获取响应
        response = await agent.invoke(messages=user_input)
        print(f"助手: {response}")
        
    except Exception as e:
        print(f"❌ 千问演示失败: {e}")


async def demo_multi_agent_conversation():
    """演示多智能体对话"""
    print("\n🤖 多智能体对话演示")
    print("=" * 40)
    
    try:
        # 创建两个智能体
        if os.getenv("AZURE_OPENAI_API_KEY"):
            agent1 = await create_azure_chat_agent(
                name="Azure-Expert",
                instructions="你是一个技术专家，专门回答技术问题。请保持简洁专业。"
            )
        else:
            agent1 = await create_qwen_chat_agent(
                name="Qwen-Expert",
                instructions="你是一个技术专家，专门回答技术问题。请保持简洁专业。"
            )
        
        if os.getenv("DASHSCOPE_API_KEY"):
            agent2 = await create_qwen_chat_agent(
                name="Qwen-Teacher",
                instructions="你是一个耐心的老师，擅长用简单易懂的方式解释复杂概念。"
            )
        else:
            agent2 = await create_azure_chat_agent(
                name="Azure-Teacher", 
                instructions="你是一个耐心的老师，擅长用简单易懂的方式解释复杂概念。"
            )
        
        print(f"✅ 创建智能体: {agent1.name}, {agent2.name}")
        
        # 模拟对话
        topic = "什么是深度学习？"
        print(f"\n话题: {topic}")
        
        # 专家回答
        expert_response = await agent1.invoke(messages=f"请简要解释：{topic}")
        print(f"\n{agent1.name}: {expert_response}")
        
        # 老师基于专家回答进行补充
        teacher_prompt = f"基于以下专家的回答，请用更通俗易懂的方式向初学者解释深度学习：\\n\\n专家回答：{expert_response}"
        teacher_response = await agent2.invoke(messages=teacher_prompt)
        print(f"\n{agent2.name}: {teacher_response}")
        
    except Exception as e:
        print(f"❌ 多智能体演示失败: {e}")


async def main():
    """主函数"""
    print("🚀 基于 Semantic Kernel 的多智能体系统演示")
    print("=" * 50)
    
    # 检查环境配置
    has_azure = bool(os.getenv("AZURE_OPENAI_API_KEY"))
    has_qwen = bool(os.getenv("DASHSCOPE_API_KEY"))
    
    print(f"Azure OpenAI 配置: {'✅' if has_azure else '❌'}")
    print(f"千问配置: {'✅' if has_qwen else '❌'}")
    
    if not has_azure and not has_qwen:
        print("❌ 请配置至少一个 LLM 服务的 API 密钥")
        return
    
    # 运行演示
    if has_azure:
        await demo_azure_agent()
    
    if has_qwen:
        await demo_qwen_agent()
    
    # 多智能体对话演示
    if has_azure or has_qwen:
        await demo_multi_agent_conversation()
    
    print("\n✨ 演示完成！")


if __name__ == "__main__":
    asyncio.run(main())