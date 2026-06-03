import json
from dataclasses import dataclass
from typing import AsyncGenerator

from app.agent.memory import ConversationMemory
from app.config import get_llm_model
from app.services.llm import llm_client
from app.tools.registry import global_registry

SYSTEM_PROMPT = """你是一个专业的 Study Agent，帮助大学生进行课程复习。

你的能力包括：
1. 从课程资料中检索知识点（search_course_material）
2. 自动提取知识点（extract_knowledge_points）
3. 生成复习提纲（generate_review_outline）
4. 生成练习题（generate_questions）
5. 评估学生答案（evaluate_answer）
6. 分析薄弱知识点（diagnose_weaknesses）
7. 制定个性化学习计划（create_study_plan）

在与学生交流时：
- 首先理解学生的学习需求
- 根据需求选择调用合适的工具
- 如果学生说"帮我复习XX"，先检索相关资料，再生成复习提纲和题目
- 如果学生提交答案，先评估，再分析薄弱点
- 如果学生问"我哪里学得不好"，查询答题记录并分析薄弱点
- 给出具体、可操作的建议，不要空洞的鼓励
- 用中文回复"""


@dataclass
class AgentController:
    memory: ConversationMemory
    course_id: str = ""
    user_id: str = "default"

    def __post_init__(self):
        context = SYSTEM_PROMPT
        if self.course_id:
            context += f"\n\n当前上下文：\n- 课程ID (course_id): {self.course_id}\n- 用户ID (user_id): {self.user_id}\n\n当学生没有明确指定课程时，使用当前上下文中的 course_id。"
        self.memory.add("system", context)

    async def run(self, user_message: str) -> str:
        """Run agent loop and return final response."""
        self.memory.add("user", user_message)

        model = get_llm_model()
        for _ in range(8):
            response = await llm_client.chat.completions.create(
                model=model,
                messages=self.memory.get_messages(),
                tools=global_registry.get_all(),
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                self.memory.add("assistant", msg.content or "", tool_calls=[
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ])

                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = await global_registry.execute(tc.function.name, args)
                    self.memory.add("tool", result, tool_call_id=tc.id, name=tc.function.name)

                # Continue loop for possible next tool call
                continue
            else:
                self.memory.add("assistant", msg.content or "")
                return msg.content or "抱歉，我无法处理你的请求。"

        return "任务执行步骤过多，请尝试更具体的提问。"

    async def run_stream(self, user_message: str) -> AsyncGenerator[dict, None]:
        self.memory.add("user", user_message)

        model = get_llm_model()
        for iteration in range(8):
            response = await llm_client.chat.completions.create(
                model=model,
                messages=self.memory.get_messages(),
                tools=global_registry.get_all() if iteration < 6 else None,
                tool_choice="auto" if iteration < 6 else "none",
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                self.memory.add("assistant", msg.content or "", tool_calls=[
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ])

                for tc in msg.tool_calls:
                    yield {
                        "type": "tool_call",
                        "tool_name": tc.function.name,
                        "tool_args": json.loads(tc.function.arguments),
                    }
                    args = json.loads(tc.function.arguments)
                    result = await global_registry.execute(tc.function.name, args)
                    yield {
                        "type": "tool_result",
                        "tool_name": tc.function.name,
                        "tool_result": result[:2000],
                    }
                    self.memory.add("tool", result, tool_call_id=tc.id, name=tc.function.name)
            else:
                content = msg.content or "抱歉，我无法处理你的请求。"
                self.memory.add("assistant", content)
                yield {"type": "text", "content": content}
                yield {"type": "done"}
                return

        yield {"type": "text", "content": "任务执行步骤过多，请尝试更具体的提问。"}
        yield {"type": "done"}


# Session-based agent instances
_agents: dict[str, AgentController] = {}


def get_agent(session_id: str) -> AgentController:
    if session_id not in _agents:
        _agents[session_id] = AgentController(memory=ConversationMemory())
    return _agents[session_id]


def reset_agent(session_id: str):
    if session_id in _agents:
        del _agents[session_id]
