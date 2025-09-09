"""
反思范式实现
"""
from typing import Any, Dict, List, Optional
from ...core.base.pattern import BasePattern, PatternType, PatternConfig
from ...core.base.agent import BaseAgent
from ...core.base.message import Message, MessageType, MessageBuilder
from .reflection_agent import ReflectionAgent


class ReflectionPatternConfig(PatternConfig):
    """反思范式配置"""
    max_reflection_rounds: int = 3
    reflection_threshold: float = 0.8
    enable_cross_agent_reflection: bool = False
    reflection_topics: List[str] = []


class ReflectionPattern(BasePattern):
    """反思范式
    
    支持智能体对自己的输出进行反思和改进
    """
    
    def __init__(self, config: ReflectionPatternConfig, llm_service):
        super().__init__(
            pattern_type=PatternType.REFLECTION,
            config=config,
            agents=[]
        )
        self.llm_service = llm_service
        self.reflection_sessions: Dict[str, Dict[str, Any]] = {}
        
    async def execute(self, input_data: Any) -> Any:
        """执行反思范式"""
        if not self.agents:
            raise ValueError("没有可用的智能体")
        
        # 如果输入是消息
        if isinstance(input_data, Message):
            return await self._process_message_with_reflection(input_data)
        
        # 如果输入是字符串
        elif isinstance(input_data, str):
            message = MessageBuilder()\
                .type(MessageType.TEXT)\
                .content(input_data)\
                .sender("user", "User")\
                .build()
            
            return await self._process_message_with_reflection(message)
        
        else:
            raise ValueError(f"不支持的输入类型: {type(input_data)}")
    
    async def coordinate_agents(self, task: Any) -> Any:
        """协调智能体进行反思"""
        results = {}
        
        for agent in self.agents:
            if isinstance(agent, ReflectionAgent):
                result = await agent.process_message(task)
                results[agent.id] = {
                    "response": result,
                    "reflection_summary": agent.get_reflection_summary()
                }
            else:
                # 普通智能体也可以参与反思过程
                result = await agent.process_message(task)
                results[agent.id] = {"response": result}
        
        # 如果启用跨智能体反思
        if self.config.enable_cross_agent_reflection:
            results = await self._perform_cross_agent_reflection(results, task)
        
        return results
    
    async def _process_message_with_reflection(self, message: Message) -> Dict[str, Any]:
        """处理带反思的消息"""
        session_id = f"session_{message.id}"
        self.reflection_sessions[session_id] = {
            "original_message": message,
            "responses": {},
            "reflection_rounds": 0,
            "final_result": None
        }
        
        # 让每个智能体处理消息
        for agent in self.agents:
            response = await agent.process_message(message)
            self.reflection_sessions[session_id]["responses"][agent.id] = response
        
        # 汇总结果
        session = self.reflection_sessions[session_id]
        session["final_result"] = await self._synthesize_responses(session["responses"])
        
        return {
            "session_id": session_id,
            "original_message": message.dict(),
            "agent_responses": {aid: resp.dict() for aid, resp in session["responses"].items()},
            "final_result": session["final_result"],
            "reflection_summary": self._get_session_reflection_summary(session_id)
        }
    
    async def _perform_cross_agent_reflection(
        self, 
        results: Dict[str, Any], 
        original_task: Any
    ) -> Dict[str, Any]:
        """执行跨智能体反思"""
        # 收集所有智能体的回应
        all_responses = []
        for agent_id, result in results.items():
            if "response" in result:
                all_responses.append({
                    "agent_id": agent_id,
                    "response": result["response"]
                })
        
        # 让每个智能体对其他智能体的回应进行反思
        cross_reflections = {}
        
        for agent in self.agents:
            if isinstance(agent, ReflectionAgent):
                reflection_prompt = self._create_cross_reflection_prompt(
                    original_task, 
                    all_responses, 
                    agent.id
                )
                
                reflection_message = MessageBuilder()\
                    .type(MessageType.SYSTEM)\
                    .content(reflection_prompt)\
                    .sender("system", "System")\
                    .recipient(agent.id, agent.name)\
                    .build()
                
                reflection_result = await agent.process_message(reflection_message)
                cross_reflections[agent.id] = reflection_result
        
        # 将跨智能体反思结果添加到原始结果
        for agent_id in results:
            if agent_id in cross_reflections:
                results[agent_id]["cross_reflection"] = cross_reflections[agent_id]
        
        return results
    
    def _create_cross_reflection_prompt(
        self, 
        original_task: Any, 
        all_responses: List[Dict[str, Any]], 
        current_agent_id: str
    ) -> str:
        """创建跨智能体反思提示"""
        responses_text = ""
        for i, resp in enumerate(all_responses, 1):
            if resp["agent_id"] != current_agent_id:
                responses_text += f"\n智能体 {i} 的回应：\n{resp['response']}\n"
        
        prompt = f"""
        请对以下其他智能体的回应进行反思和评估：
        
        原始任务：{original_task}
        
        其他智能体的回应：{responses_text}
        
        请从以下角度进行反思：
        1. 这些回应有什么优点？
        2. 是否有遗漏或可以改进的地方？
        3. 你会如何补充或改进这些回应？
        4. 有没有发现新的见解或观点？
        
        请提供你的反思和建议：
        """
        
        return prompt
    
    async def _synthesize_responses(self, responses: Dict[str, Message]) -> Dict[str, Any]:
        """综合多个智能体的回应"""
        if not responses:
            return {"synthesized_response": "没有收到任何回应"}
        
        # 简单的综合策略：选择最长的回应作为主要回应
        main_response = max(responses.values(), key=lambda msg: len(msg.get_text_content()))
        
        # 收集所有回应的元数据
        metadata_summary = {}
        for agent_id, response in responses.items():
            metadata_summary[agent_id] = response.metadata
        
        return {
            "synthesized_response": main_response.get_text_content(),
            "main_agent": main_response.sender_id,
            "all_responses_count": len(responses),
            "metadata_summary": metadata_summary
        }
    
    def _get_session_reflection_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话反思总结"""
        if session_id not in self.reflection_sessions:
            return {}
        
        session = self.reflection_sessions[session_id]
        
        # 统计反思相关信息
        total_reflection_rounds = 0
        reflection_agents = 0
        
        for agent_id, response in session["responses"].items():
            if "reflection_rounds" in response.metadata:
                total_reflection_rounds += response.metadata["reflection_rounds"]
                reflection_agents += 1
        
        return {
            "session_id": session_id,
            "total_agents": len(session["responses"]),
            "reflection_agents": reflection_agents,
            "total_reflection_rounds": total_reflection_rounds,
            "avg_reflection_rounds": total_reflection_rounds / reflection_agents if reflection_agents > 0 else 0,
            "cross_agent_reflection_enabled": self.config.enable_cross_agent_reflection
        }
    
    def create_reflection_agent(
        self, 
        name: str, 
        max_reflection_rounds: Optional[int] = None,
        reflection_threshold: Optional[float] = None
    ) -> ReflectionAgent:
        """创建并添加反思智能体"""
        agent = ReflectionAgent(
            name=name,
            llm_service=self.llm_service,
            max_reflection_rounds=max_reflection_rounds or self.config.max_reflection_rounds,
            reflection_threshold=reflection_threshold or self.config.reflection_threshold
        )
        
        self.add_agent(agent)
        return agent
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """获取范式统计信息"""
        reflection_agents = [agent for agent in self.agents if isinstance(agent, ReflectionAgent)]
        
        total_reflections = 0
        for agent in reflection_agents:
            total_reflections += len(agent.reflection_history)
        
        return {
            "total_agents": len(self.agents),
            "reflection_agents": len(reflection_agents),
            "total_sessions": len(self.reflection_sessions),
            "total_reflections": total_reflections,
            "config": self.config.dict()
        }