"""
基于 Semantic Kernel 的反思智能体演示
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core.services.sk_azure_service import get_azure_service_manager
from core.services.sk_qwen_service import get_qwen_service_manager
from patterns.reflection.reflection_agent import SKReflectionAgent


async def main():
    """主函数"""
    print("🤖 基于 Semantic Kernel 的反思智能体演示")
    print("=" * 50)
    
    # 检查环境配置
    has_azure = bool(os.getenv("AZURE_OPENAI_API_KEY"))
    has_qwen = bool(os.getenv("DASHSCOPE_API_KEY"))
    
    print(f"Azure OpenAI 配置: {'✅' if has_azure else '❌'}")
    print(f"千问配置: {'✅' if has_qwen else '❌'}")
    
    if not has_azure and not has_qwen:
        print("❌ 请配置至少一个 LLM 服务的 API 密钥")
        return
    
    # 选择服务
    service_type = input("请选择服务 (1: Azure OpenAI, 2: 千问): ").strip()
    
    try:
        if service_type == "1" and has_azure:
            print("正在初始化 Azure OpenAI 服务...")
            service_manager = await get_azure_service_manager()
            chat_service = service_manager.get_chat_service()
            kernel = service_manager.get_kernel()
            
        elif service_type == "2" and has_qwen:
            print("正在初始化千问服务...")
            service_manager = await get_qwen_service_manager()
            chat_service = service_manager.get_chat_service()
            kernel = service_manager.get_kernel()
            
        else:
            print("使用默认可用服务...")
            if has_azure:
                service_manager = await get_azure_service_manager()
                chat_service = service_manager.get_chat_service()
                kernel = service_manager.get_kernel()
            else:
                service_manager = await get_qwen_service_manager()
                chat_service = service_manager.get_chat_service()
                kernel = service_manager.get_kernel()
        
        print(f"✅ 服务初始化成功: {service_manager.get_service_info()}")
        
        # 创建反思智能体
        reflection_agent = SKReflectionAgent(
            name="深度反思者",
            service=chat_service,
            max_reflection_rounds=3,
            reflection_threshold=0.8,
            kernel=kernel
        )
        
        print(f"✅ 创建反思智能体: {reflection_agent.name}")
        
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
                # 处理消息
                response = await reflection_agent.process_message(user_input)
                
                print(f"\n📝 {reflection_agent.name}: {response.content}")
                
                # 显示反思信息
                metadata = response.metadata
                if metadata:
                    print(f"\n🔍 反思信息:")
                    print(f"- 反思轮次: {metadata.get('reflection_rounds', 0)}")
                    print(f"- 最终质量分数: {metadata.get('final_quality_score', 'N/A')}")
                    
                    reflection_process = metadata.get('reflection_process', [])
                    if reflection_process:
                        print(f"- 反思过程:")
                        for i, process in enumerate(reflection_process, 1):
                            print(f"  轮次 {i}: {process.get('evaluation', {}).get('overall_score', 'N/A')}")
                
            except Exception as e:
                print(f"❌ 处理过程中出现错误: {e}")
        
        # 显示反思历史摘要
        print(f"\n📊 反思历史摘要:")
        summary = reflection_agent.get_reflection_summary()
        print(f"- 总反思次数: {summary['total_reflections']}")
        print(f"- 平均反思轮次: {summary['avg_improvement_rounds']:.1f}")
        print(f"- 反思配置: 最大轮次={summary['reflection_config']['max_rounds']}, 阈值={summary['reflection_config']['threshold']}")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
    
    finally:
        print("\n👋 感谢使用基于 Semantic Kernel 的反思智能体系统！")


if __name__ == "__main__":
    asyncio.run(main())