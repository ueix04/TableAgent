"""对话历史管理。"""

from typing import Any


class ConversationMemory:
    """管理 messages 列表，追加、截断、重置。"""

    def __init__(self, system_prompt: str):
        self._messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    @property
    def messages(self) -> list[dict[str, Any]]:
        return self._messages

    def add_user(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str | None) -> None:
        self._messages.append({"role": "assistant", "content": content})

    def add_tool(self, content: str, tool_call_id: str) -> None:
        self._messages.append(
            {"role": "tool", "content": content, "tool_call_id": tool_call_id}
        )

    def pop_last(self) -> dict[str, Any] | None:
        if len(self._messages) > 1:
            return self._messages.pop()
        return None

    def trim(self, max_tokens: int = 128000) -> None:
        """简单截断：保留 system 消息，移除最早的非 system 消息直到低于限制。
        实际项目中可用 tiktoken 精确计算，这里以字符数近似估算。"""
        if self._char_count() <= max_tokens:
            return
        while self._char_count() > max_tokens and len(self._messages) > 2:
            # 保留 system（index 0），移除最旧的 user/assistant 轮次
            for i in range(1, len(self._messages) - 1):
                if self._messages[i]["role"] in ("user", "assistant"):
                    self._messages.pop(i)
                    break

    def _char_count(self) -> int:
        return sum(len(str(m.get("content", ""))) for m in self._messages)

    def reset(self) -> None:
        system = self._messages[0]
        self._messages = [system]
