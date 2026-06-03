from __future__ import annotations
"""Simple conversation memory: stores recent messages for agent context."""

MAX_HISTORY = 20


class ConversationMemory:
    def __init__(self):
        self.messages: list[dict] = []

    def add(self, role: str, content: str, tool_calls: list | None = None, tool_call_id: str | None = None, name: str | None = None):
        msg = {"role": role}
        if content:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        if name:
            msg["name"] = name
        self.messages.append(msg)

        if len(self.messages) > MAX_HISTORY * 2:
            # Keep system message + last N messages
            system = [m for m in self.messages if m["role"] == "system"]
            rest = [m for m in self.messages if m["role"] != "system"]
            self.messages = system + rest[-MAX_HISTORY:]

    def get_messages(self) -> list[dict]:
        return self.messages

    def clear(self):
        self.messages = []


class LearningState:
    """Tracks student learning progress per course."""

    def __init__(self):
        self.state: dict = {}  # {course_id: {knowledge_point: {total, correct, wrong}}}

    def record_answer(self, course_id: str, knowledge_point: str, is_correct: bool):
        if course_id not in self.state:
            self.state[course_id] = {}
        kp = self.state[course_id].setdefault(knowledge_point, {"total": 0, "correct": 0, "wrong": 0})
        kp["total"] += 1
        if is_correct:
            kp["correct"] += 1
        else:
            kp["wrong"] += 1

    def get_weak_points(self, course_id: str, threshold: float = 0.4) -> list[dict]:
        course_state = self.state.get(course_id, {})
        weak = []
        for kp, s in course_state.items():
            if s["total"] >= 3:  # need at least 3 attempts
                error_rate = s["wrong"] / s["total"]
                if error_rate >= threshold:
                    weak.append({"knowledge_point": kp, "error_rate": error_rate, **s})
        return sorted(weak, key=lambda x: x["error_rate"], reverse=True)
