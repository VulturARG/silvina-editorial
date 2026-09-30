from typing import Any

from laya.agent import Agent


class FakeLayaAgent(Agent):
    """Laya agent double returning configured answers without loading a checkpoint."""

    def __init__(self, answers: dict[str, dict[str, Any]]) -> None:
        self._answers = answers
        self.received_states: list[Any] = []
        self.received_questions: list[dict[str, dict[str, Any]]] = []

    def predict(
        self, state: Any, questions: dict[str, dict[str, Any]], **kwargs: Any
    ) -> dict[str, Any]:
        self.received_states.append(state)
        self.received_questions.append(questions)
        return {"answers": self._answers, "usage": {}}
