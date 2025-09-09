"""
反思模式演示示例
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core.services.azure_service import AzureLLMService
from core.services.qwen_service import QwenLLMService
from patterns.reflection.reflection_pattern import ReflectionPattern, ReflectionPatternConfig


async def main():
    """反思模式演示"""
    
    print("🤖 多智能体系统 - 反思模式演示")
    print("=" * 50)
    
    # 选择 LLM 服务
    service_type = input("请选择 LLM 服务 (1: Azure OpenAI, 2: 阿里千问): ").strip()
    
    if service_type == "1":
        print("正在初始化 Azure OpenAI 服务...")
        llm_service = AzureLLMService()
    elif service_type == "2":
        print("正在初始化阿里千问服务...")
        llm_service = QwenLLMService()
    else:
        print("无效选择，使用默认的 Azure OpenAI 服务")
        llm_service = AzureLLMService()
    
    try:
        # 初始化服务
        await llm_service.initialize()
        
        if not llm_service.is_available:
            print("❌ LLM 服务初始化失败，请检查配置")
            return
        
        print(f"✅ LLM 服务初始化成功: {llm_service.get_model_info()}")
        
        # 创建反思范式配置
        config = ReflectionPatternConfig(
            name="智能反思助手",
            description="具备自我反思和改进能力的智能体系统",
            max_reflection_rounds=3,
            reflection_threshold=0.7,
            enable_cross_agent_reflection=True
        )
        
        # 创建反思范式
        reflection_pattern = ReflectionPattern(config, llm_service)
        
        # 创建多个反思智能体
        agent1 = reflection_pattern.create_reflection_agent(
            name="深度思考者",
            max_reflection_rounds=3,
            reflection_threshold=0.8
        )
        
        agent2 = reflection_pattern.create_reflection_agent(
            name="批判性分析师",
            max_reflection_rounds=2,
            reflection_threshold=0.75
        )
        
        print(f"✅ 创建了 {len(reflection_pattern.agents)} 个反思智能体")
        
        # 激活范式
        reflection_pattern.activate()
        print("✅ 反思范式已激活")
        
        # 交互式对话
        print("\n🔄 开始反思对话 (输入 'quit' 退出)")
        print("-" * 30)
        
        while True:
            user_input = input("\n用户: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not user_input:
                continue
            
            print("\n🤔 智能体正在思考和反思...")
            
            try:
                # 执行反思范式
                result = await reflection_pattern.execute(user_input)
                
                print(f"\n📝 处理结果:")
                print(f"会话ID: {result['session_id']}")
                print(f"最终回答: {result['final_result']['synthesized_response']}")
                
                # 显示反思摘要
                reflection_summary = result['reflection_summary']
                print(f"\n🔍 反思摘要:")
                print(f"- 参与智能体: {reflection_summary['total_agents']}")
                print(f"- 反思智能体: {reflection_summary['reflection_agents']}")
                print(f"- 总反思轮次: {reflection_summary['total_reflection_rounds']}")
                print(f"- 平均反思轮次: {reflection_summary['avg_reflection_rounds']:.1f}")
                
                # 显示各智能体的详细反思信息
                for agent_id, response_data in result['agent_responses'].items():
                    agent_name = next((agent.name for agent in reflection_pattern.agents if agent.id == agent_id), "Unknown")
                    metadata = response_data.get('metadata', {})
                    
                    if 'reflection_rounds' in metadata:
                        print(f"\n🧠 {agent_name} 的反思过程:")
                        print(f"  - 反思轮次: {metadata['reflection_rounds']}")
                        print(f"  - 最终质量分数: {metadata.get('final_quality_score', 'N/A')}")
                
            except Exception as e:
                print(f"❌ 处理过程中出现错误: {e}")
        
        # 显示最终统计
        print("\n📊 最终统计信息:")
        stats = reflection_pattern.get_pattern_statistics()
        print(f"- 总智能体数: {stats['total_agents']}")
        print(f"- 反思智能体数: {stats['reflection_agents']}")
        print(f"- 总会话数: {stats['total_sessions']}")
        print(f"- 总反思次数: {stats['total_reflections']}")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
    
    finally:
        # 清理资源
        await llm_service.close()
        print("\n👋 感谢使用多智能体反思系统！")


if __name__ == "__main__":
    asyncio.run(main())