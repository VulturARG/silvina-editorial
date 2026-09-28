from unittest import TestCase
from unittest.mock import MagicMock

from src.domain.classification.article_classification_response_parser import (
    ArticleClassificationResponseParser,
)
from src.domain.classification.research_intent_detector_port import (
    ResearchIntentDetectorPort,
)
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.tests.classification.fake_llm_generator_adapter import (
    FakeLlmGeneratorAdapter,
)
from src.infrastructure.adapters.classification.ollama_research_intent_adapter import (
    OllamaResearchIntentAdapter,
)


class TestOllamaResearchIntentAdapter(TestCase):
    def setUp(self) -> None:
        self.signal_prompt_template = (
            "Title: {title}\nText: {text_sample}\nRespond with S4, S5, S6."
        )
        self.response_parser = ArticleClassificationResponseParser()

    def test_is_subclass_of_research_intent_detector_port(self) -> None:
        self.assertTrue(issubclass(OllamaResearchIntentAdapter, ResearchIntentDetectorPort))

    def test_detect_formats_prompt_and_passes_default_options(self) -> None:
        llm_generator = FakeLlmGeneratorAdapter(responses=["S4: SI\nS5: NO\nS6: SI"])
        adapter = OllamaResearchIntentAdapter(
            llm_generator=llm_generator,
            response_parser=self.response_parser,
            signal_prompt_template=self.signal_prompt_template,
        )

        result = adapter.detect(
            text_sample="Investigamos los efectos del compuesto.",
            title="Efectos del compuesto",
        )

        expected_prompt = (
            "Title: Efectos del compuesto\n"
            "Text: Investigamos los efectos del compuesto.\n"
            "Respond with S4, S5, S6."
        )
        self.assertEqual(llm_generator.received_prompts, [expected_prompt])
        self.assertEqual(
            llm_generator.received_options,
            [{"temperature": 0.1, "num_predict": 150}],
        )
        self.assertEqual(result, (True, False, True))

    def test_detect_passes_custom_temperature_and_num_predict_options(self) -> None:
        llm_generator = FakeLlmGeneratorAdapter(responses=["S4: NO\nS5: NO\nS6: NO"])
        adapter = OllamaResearchIntentAdapter(
            llm_generator=llm_generator,
            response_parser=self.response_parser,
            signal_prompt_template=self.signal_prompt_template,
            temperature=0.2,
            num_predict=300,
        )

        result = adapter.detect(
            text_sample="Un ensayo breve sobre literatura.",
            title="Ensayo literario",
        )

        self.assertEqual(
            llm_generator.received_options,
            [{"temperature": 0.2, "num_predict": 300}],
        )
        self.assertEqual(result, (False, False, False))

    def test_detect_formats_prompt_when_title_is_none(self) -> None:
        llm_generator = FakeLlmGeneratorAdapter(responses=["S4: SI\nS5: SI\nS6: SI"])
        adapter = OllamaResearchIntentAdapter(
            llm_generator=llm_generator,
            response_parser=self.response_parser,
            signal_prompt_template=self.signal_prompt_template,
        )

        result = adapter.detect(
            text_sample="Metodologia y recoleccion de datos cuantitativos.",
            title=None,
        )

        expected_prompt = (
            "Title: None\n"
            "Text: Metodologia y recoleccion de datos cuantitativos.\n"
            "Respond with S4, S5, S6."
        )
        self.assertEqual(llm_generator.received_prompts, [expected_prompt])
        self.assertEqual(result, (True, True, True))

    def test_detect_propagates_exception_when_llm_generator_raises(self) -> None:
        failing_generator = MagicMock(spec=LlmGeneratorPort)
        failing_generator.generate.side_effect = RuntimeError("Ollama connection error")

        adapter = OllamaResearchIntentAdapter(
            llm_generator=failing_generator,
            response_parser=self.response_parser,
            signal_prompt_template=self.signal_prompt_template,
        )

        with self.assertRaises(RuntimeError):
            adapter.detect(
                text_sample="Texto de prueba.",
                title="Titulo de prueba",
            )
