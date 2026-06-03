from __future__ import annotations
from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    question_type: str = Field(description="题型: single_choice | short_answer | true_false")
    stem: str = Field(description="题干")
    options: dict = Field(default_factory=dict, description="选择题选项 {'A': '...', 'B': '...'}")
    answer: str = Field(description="标准答案")
    explanation: str = Field(description="答案解析，解释为什么这个答案正确")
    knowledge_point: str = Field(description="对应知识点")
    difficulty: str = Field(description="难度: easy / medium / hard")


class QuestionGenerationResult(BaseModel):
    questions: list[QuestionItem] = Field(description="生成的题目列表")


# ── Prompt for regular practice questions (uses document chunks) ──

async def generate_questions(
    chunks: list[dict],
    knowledge_point: str = "",
    question_type: str = "single_choice",
    count: int = 5,
    difficulty: str = "medium",
) -> list[QuestionItem]:
    from app.services.llm import structured_completion

    context = "\n\n".join(
        f"[来源: {c.get('source', '未知')}]\n{c['content']}" for c in chunks
    )

    type_instruction = ""
    if question_type == "single_choice":
        type_instruction = "生成单选题：每题4个选项（A/B/C/D），只有一个正确答案。选项用字典格式。"
    elif question_type == "short_answer":
        type_instruction = "生成简答题：学生需自己写出答案，答案要包含关键得分点。"
    elif question_type == "true_false":
        type_instruction = "生成判断正误题：陈述一个命题，学生判断对错并说明理由。"

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位专业的课程题库设计专家。你需要根据提供的课程资料生成高质量的练习题。"
                "题目要基于资料内容，考察学生对知识点的理解和应用能力。"
                f"{type_instruction}"
                "每个题目必须包含答案解析，解释为什么这个答案正确。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"知识点：{knowledge_point or '综合'}\n"
                f"题型：{question_type}\n"
                f"数量：{count} 题\n"
                f"难度：{difficulty}\n\n"
                f"课程资料内容：\n{context}\n\n"
                f"请基于以上资料生成 {count} 道{question_type}题目。"
            ),
        },
    ]

    result = await structured_completion(messages, QuestionGenerationResult, temperature=0.7, max_tokens=4096)
    return result.questions


# ── Exam paper generation: Chinese university final exam style ──

class ExamQuestionsResult(BaseModel):
    choice_questions: list[QuestionItem] = Field(default_factory=list)
    short_answer_questions: list[QuestionItem] = Field(default_factory=list)
    true_false_questions: list[QuestionItem] = Field(default_factory=list)


EXAM_SYSTEM_PROMPT = """你是一位中国大学工科期末考试命题专家。你需要根据课程的知识点大纲，生成一份完整的期末试卷。

## 命题原则
1. **选择题**：考察学生对核心概念、原理、方法的准确理解。选项应有干扰性，不能太明显。每题4个选项（A/B/C/D）。
2. **简答题**：考察学生的实操能力和对原理的深度理解。参考中国大学工科期末考试风格：
   - "简述XXX的工作流程/步骤"
   - "说明XXX与YYY的区别和适用场景"
   - "在什么条件下应该使用XXX？为什么？"
   - "分析XXX问题的原因及解决方案"
   - 答案要包含关键得分点，分条列出
   - **不要出纯记忆性的题**（如"XXX的定义是什么"），要出需要理解和分析的题
3. **判断题**（如有）：陈述一个可能正确或错误的命题，正确答案为"正确"或"错误"，解析要说明原因。

## 难度分布
- easy（基础）：考察基本概念和常见操作，30%
- medium（中等）：考察原理理解和综合运用，50%
- hard（困难）：考察分析能力和实际问题的解决，20%

## 输出格式
所有题目必须包含：question_type, stem, options(选择题), answer, explanation, knowledge_point, difficulty"""


async def generate_exam_questions(
    knowledge_points: list[str],
    choice_count: int = 20,
    short_answer_count: int = 5,
    true_false_count: int = 0,
    difficulty_distribution: dict | None = None,
) -> "ExamQuestionsResult":
    from app.services.llm import structured_completion

    points_text = "\n".join(f"- {p}" for p in knowledge_points) if knowledge_points else "综合"

    requirements = [
        f"生成 {choice_count} 道单选题",
        f"生成 {short_answer_count} 道简答题（工科实操风格）",
    ]
    if true_false_count > 0:
        requirements.append(f"生成 {true_false_count} 道判断正误题")

    user_msg = f"""知识点大纲：
{points_text}

要求：
{chr(10).join(f'- {r}' for r in requirements)}

难度分布：简单30%、中等50%、困难20%

请生成一份完整的期末试卷题目。"""

    result = await structured_completion(
        [{"role": "system", "content": EXAM_SYSTEM_PROMPT}, {"role": "user", "content": user_msg}],
        ExamQuestionsResult,
        temperature=0.8,
        max_tokens=8192,
    )
    return result
