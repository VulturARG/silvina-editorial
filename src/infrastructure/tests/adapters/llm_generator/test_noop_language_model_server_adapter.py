from unittest import TestCase

from src.domain.language_model.language_model_server_port import LanguageModelServerPort
from src.infrastructure.adapters.llm_generator.noop_language_model_server_adapter import (
    NoOpLanguageModelServerAdapter,
)


class TestNoOpLanguageModelServerAdapter(TestCase):
    def test_is_subclass_of_language_model_server_port(self):
        self.assertTrue(issubclass(NoOpLanguageModelServerAdapter, LanguageModelServerPort))

    def test_is_running_returns_true(self):
        adapter = NoOpLanguageModelServerAdapter()

        self.assertTrue(adapter.is_running())

    def test_start_does_nothing(self):
        adapter = NoOpLanguageModelServerAdapter()

        adapter.start()

    def test_mark_in_use_does_nothing(self):
        adapter = NoOpLanguageModelServerAdapter()

        adapter.mark_in_use()

    def test_mark_idle_does_nothing(self):
        adapter = NoOpLanguageModelServerAdapter()

        adapter.mark_idle()
