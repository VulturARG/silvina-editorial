from unittest import TestCase

from src.domain.language_model.language_model_warmup_port import LanguageModelWarmupPort
from src.infrastructure.adapters.llm_generator.noop_language_model_warmup_adapter import (
    NoOpLanguageModelWarmupAdapter,
)


class TestNoOpLanguageModelWarmupAdapter(TestCase):
    def test_implements_language_model_warmup_port(self):
        adapter = NoOpLanguageModelWarmupAdapter()

        self.assertIsInstance(adapter, LanguageModelWarmupPort)

    def test_warm_up_does_nothing(self):
        adapter = NoOpLanguageModelWarmupAdapter()

        result = adapter.warm_up()

        self.assertIsNone(result)
