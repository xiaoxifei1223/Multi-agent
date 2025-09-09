"""
基于 Semantic Kernel 的反思智能体实现
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel import Kernel

from ...core.base.agent import BaseAgent, AgentRole, AgentStatus
from ...core.base.message import Message, MessageType, MessageBuilder


class SKReflectionAgent(BaseAgent):
    """反思智能体 - 基于 Semantic Kernel
    
    能够对自己的输出进行反思和改进的智能体
    """
    
    def __init__(
        self,
        name: str,
        service: ChatCompletionClientBase,
        max_reflection_rounds: int = 3,
        reflection_threshold: float = 0.8,
        kernel: Optional[Kernel] = None
    ):
        # 基本指令
        instructions = f"""
        你是一个具备反思能力的智能助手。你的任务是：
        1. 仔细分析用户的问题
        2. 提供最初的回答
        3. 对自己的回答进行评估和反思
        4. 根据反思结果改进回答
        5. 重复反思过程直到达到满意的质量
        
        请始终保持客观、严谨的态度，不断改进你的回答质量。
        """
        
        super().__init__(
            name=name,
            role=AgentRole.ASSISTANT,
            service=service,
            instructions=instructions,
            description="具备反思和自我改进能力的智能体",
            capabilities=["reflection", "self_improvement", "iterative_thinking"],
            kernel=kernel
        )
        
        self.max_reflection_rounds = max_reflection_rounds
        self.reflection_threshold = reflection_threshold
        self.reflection_history: List[Dict[str, Any]] = []
        
        # 创建评估智能体（用于评估回答质量）
        evaluator_instructions = """
        你是一个专业的回答质量评估专家。请从以下维度评估回答：
        1. 相关性（是否直接相关于问题）
        2. 准确性（是否准确无误）
        3. 完整性（是否充分完整）
        4. 清晰性（是否清晰易懂）
        5. 有用性（是否对用户有帮助）
        
        请给出0-1的分数和具体的改进建议。
        """
        
        self.evaluator_agent = ChatCompletionAgent(
            service=service,
            name=f"{name}-Evaluator",
            instructions=evaluator_instructions,
            kernel=kernel
        )
        
    async def process_message(self, message: Union[Message, str]) -> Message:
        """处理消息，包含反思机制"""
        self.set_status(AgentStatus.THINKING)
        
        try:
            # 获取输入内容
            if isinstance(message, str):
                input_content = message
                sender_id = "user"
                sender_name = "User"
            else:
                input_content = message.get_text_content()
                sender_id = message.sender_id
                sender_name = message.sender_name
                self.add_message(message)
            
            # 生成初始响应
            current_response = await self._generate_initial_response(input_content)
            
            # 反思循环
            reflection_round = 0
            
            while reflection_round < self.max_reflection_rounds:
                reflection_round += 1
                
                # 评估当前响应
                evaluation = await self._evaluate_response(input_content, current_response)
                
                # 如果质量足够好，停止反思
                if evaluation.get("overall_score", 0) >= self.reflection_threshold:
                    break
                
                # 生成改进的响应
                improved_response = await self._improve_response(
                    input_content, 
                    current_response, 
                    evaluation
                )
                
                # 记录反思过程
                self.reflection_history.append({
                    "round": reflection_round,
                    "original_response": current_response,
                    "evaluation": evaluation,
                    "improved_response": improved_response,
                    "timestamp": datetime.now()
                })
                
                current_response = improved_response
            
            # 创建最终响应消息
            response_message = MessageBuilder()\
                .type(MessageType.TEXT)\
                .content(current_response)\
                .sender(self.id, self.name)\
                .recipient(sender_id, sender_name)\
                .metadata({
                    "reflection_rounds": reflection_round,
                    "final_quality_score": evaluation.get("overall_score", 0.0),
                    "reflection_process": self.reflection_history[-reflection_round:] if reflection_round > 0 else []
                })\
                .build()
            
            self.add_message(response_message)
            self.set_status(AgentStatus.IDLE)
            
            return response_message
            
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            error_message = MessageBuilder()\
                .type(MessageType.ERROR)\
                .content(f"反思处理失败: {str(e)}")\
                .sender(self.id, self.name)\
                .recipient(sender_id if 'sender_id' in locals() else "user", 
                          sender_name if 'sender_name' in locals() else "User")\
                .build()
            
            return error_message
    
    async def think(self, input_data: Any) -> Any:
        """思考过程"""
        # 实现具体的思考逻辑
        return await self._generate_initial_response(input_data)
    
    async def act(self, action: Dict[str, Any]) -> Any:
        """执行动作"""
        action_type = action.get("type", "")
        
        if action_type == "reflect":
            return await self._perform_reflection(action.get("target"))
        elif action_type == "improve":
            return await self._improve_response(
                action.get("original_message"),
                action.get("current_response"),
                action.get("evaluation")
            )
        else:
            return f"未知动作类型: {action_type}"
    
    async def _generate_initial_response(self, input_content: str) -> str:
        """生成初始回应 - 使用 Semantic Kernel"""
        try:
            # 使用 SK Agent 生成回应
            response = await self.sk_agent.invoke(
                messages=f"请回答以下问题：{input_content}"
            )
            
            return str(response) if response else "无法生成回应"
            
        except Exception as e:
            return f"生成回应失败：{str(e)}"
    
    async def _evaluate_response(self, original_question: str, response: str) -> Dict[str, Any]:
        """评估回应质量 - 使用 Semantic Kernel"""
        evaluation_prompt = f"""
        请评估以下回答的质量，从以下几个维度进行评分（0-1分）：
        1. 相关性：回答是否直接相关于问题
        2. 准确性：回答是否准确无误
        3. 完整性：回答是否充分完整
        4. 清晰性：回答是否清晰易懂
        5. 有用性：回答是否对用户有帮助
        
        原始问题：{original_question}
        
        回答：{response}
        
        请以JSON格式返回评估结果：
        {{
            "relevance": 0.0-1.0,
            "accuracy": 0.0-1.0,
            "completeness": 0.0-1.0,
            "clarity": 0.0-1.0,
            "usefulness": 0.0-1.0,
            "overall_score": 0.0-1.0,
            "improvement_suggestions": ["建议1", "建议2", ...]
        }}
        """
        
        try:
            # 使用评估智能体
            evaluation_response = await self.evaluator_agent.invoke(
                messages=evaluation_prompt
            )
            
            # 尝试解析JSON响应
            import json
            import re
            
            response_text = str(evaluation_response)
            
            # 提取JSON部分
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                evaluation = json.loads(json_str)
            else:
                # 如果无法解析，返回默认评估
                evaluation = {
                    "relevance": 0.7,
                    "accuracy": 0.7,
                    "completeness": 0.7,
                    "clarity": 0.7,
                    "usefulness": 0.7,
                    "overall_score": 0.7,
                    "improvement_suggestions": ["无法解析评估结果。"]
                }
            
            # 计算总体分数
            if "overall_score" not in evaluation:
                scores = [
                    evaluation.get("relevance", 0),
                    evaluation.get("accuracy", 0),
                    evaluation.get("completeness", 0),
                    evaluation.get("clarity", 0),
                    evaluation.get("usefulness", 0)
                ]
                evaluation["overall_score"] = sum(scores) / len(scores)
            
            return evaluation
            
        except Exception as e:
            # 如果评估失败，返回默认评估
            return {
                "overall_score": 0.5,
                "improvement_suggestions": [f"评估过程失败：{str(e)}"]
            }
    
    async def _improve_response(
        self, 
        original_question: str, 
        current_response: str, 
        evaluation: Dict[str, Any]
    ) -> str:
        """改进回应 - 使用 Semantic Kernel"""
        suggestions = evaluation.get("improvement_suggestions", [])
        suggestions_text = "\n".join([f"- {suggestion}" for suggestion in suggestions])
        
        improvement_prompt = f"""
        请根据以下评估反馈改进你的回答：
        
        原始问题：{original_question}
        
        当前回答：{current_response}
        
        改进建议：
        {suggestions_text}
        
        请生成一个改进后的回答，确保：
        1. 更准确地回答问题
        2. 提供更完整的信息
        3. 表达更清晰
        4. 对用户更有帮助
        
        改进后的回答：
        """
        
        try:
            # 使用 SK Agent 改进回应
            improved_response = await self.sk_agent.invoke(
                messages=improvement_prompt
            )
            
            return str(improved_response) if improved_response else current_response
            
        except Exception as e:
            # 如果改进失败，返回原回应
            return current_response
    
    async def _perform_reflection(self, target: Any) -> Dict[str, Any]:
        """执行反思过程"""
        return {
            "reflection_completed": True,
            "insights": [],
            "improvements": []
        }
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """获取反思总结"""
        return {
            "total_reflections": len(self.reflection_history),
            "recent_reflections": self.reflection_history[-5:],
            "avg_improvement_rounds": sum(r["round"] for r in self.reflection_history) / len(self.reflection_history) if self.reflection_history else 0,
            "reflection_config": {
                "max_rounds": self.max_reflection_rounds,
                "threshold": self.reflection_threshold
            }
        }