from unittest import TestCase

from src.domain.enums.app_mode import AppMode
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy
from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.domain.tests.classification.fake_llm_generator_adapter import FakeLlmGeneratorAdapter
from src.domain.tests.metrics.fake_analysis_context_port import FakeAnalysisContextPort
from src.domain.tests.metrics.fake_analysis_metrics_port import FakeAnalysisMetricsPort
from src.infrastructure.adapters.llm_generator.audited_llm_generator_adapter import (
    AuditedLlmGeneratorAdapter,
)
from src.infrastructure.tests.test_doubles.failing_llm_generator_adapter import (
    FailingLlmGeneratorAdapter,
)
from src.infrastructure.tests.test_doubles.slow_llm_generator_adapter import (
    SlowLlmGeneratorAdapter,
)


class TestAuditedLlmGeneratorAdapter(TestCase):
    """Unit tests for AuditedLlmGeneratorAdapter."""

    def setUp(self) -> None:
        self.metrics_port = FakeAnalysisMetricsPort()
        self.context_port = FakeAnalysisContextPort()
        self.context_port.set_analysis_id("analysis-test-identifier")
        self.provider = "ollama"
        self.model_name = "test-model"
        self.purpose = "classification"

    def _create_adapter(
        self,
        generator: LlmGeneratorPort,
        audit_payload_policy: AuditPayloadPolicy | None = None,
    ) -> AuditedLlmGeneratorAdapter:
        policy = (
            audit_payload_policy
            if audit_payload_policy is not None
            else AuditPayloadPolicy(app_mode=AppMode.DEBUG)
        )
        return AuditedLlmGeneratorAdapter(
            generator=generator,
            metrics_port=self.metrics_port,
            analysis_context_port=self.context_port,
            provider=self.provider,
            model_name=self.model_name,
            purpose=self.purpose,
            audit_payload_policy=policy,
        )

    def test_is_instance_of_llm_generator_port(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["expected response"])
        adapter = self._create_adapter(generator=wrapped_generator)
        self.assertIsInstance(adapter, LlmGeneratorPort)

    def test_generate_returns_wrapped_response_unchanged(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["expected response text"])
        adapter = self._create_adapter(generator=wrapped_generator)

        response = adapter.generate(prompt="test prompt")

        self.assertEqual(response, "expected response text")

    def test_generate_forwards_prompt_and_none_options_to_wrapped_generator(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["response"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="prompt with default options")

        self.assertEqual(wrapped_generator.received_prompts, ["prompt with default options"])
        self.assertEqual(wrapped_generator.received_options, [None])

    def test_generate_forwards_prompt_and_explicit_options_to_wrapped_generator(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["response"])
        adapter = self._create_adapter(generator=wrapped_generator)
        custom_options = {"temperature": 0.2, "num_predict": 150}

        adapter.generate(prompt="prompt with custom options", options=custom_options)

        self.assertEqual(wrapped_generator.received_prompts, ["prompt with custom options"])
        self.assertEqual(wrapped_generator.received_options, [custom_options])

    def test_generate_records_exactly_one_ai_interaction_on_success(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["first response"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="test prompt")

        self.assertEqual(len(self.metrics_port.recorded_ai_interactions), 1)

    def test_generate_records_ai_interaction_with_context_analysis_id_and_configured_metadata(
        self,
    ) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["generated output"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="sample prompt")

        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertEqual(recorded_interaction.analysis_id, "analysis-test-identifier")
        self.assertEqual(recorded_interaction.provider, self.provider)
        self.assertEqual(recorded_interaction.purpose, self.purpose)
        self.assertEqual(recorded_interaction.model_name, self.model_name)
        self.assertEqual(recorded_interaction.input_payload, "sample prompt")
        self.assertEqual(recorded_interaction.output_payload, "generated output")
        self.assertEqual(recorded_interaction.status, ExecutionStatus.SUCCESS)

    def test_generate_records_duration_in_milliseconds_as_non_negative_float(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["response"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="sample prompt")

        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertIsInstance(recorded_interaction.duration_ms, float)
        self.assertGreaterEqual(recorded_interaction.duration_ms, 0.0)

    def test_generate_measures_latency_with_slow_generator(self) -> None:
        slow_generator = SlowLlmGeneratorAdapter(response="delayed response", delay_seconds=0.02)
        adapter = self._create_adapter(generator=slow_generator)

        adapter.generate(prompt="sample prompt")

        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertGreaterEqual(recorded_interaction.duration_ms, 5.0)

    def test_generate_records_each_call_in_chronological_order(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["first response", "second response"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="first prompt")
        adapter.generate(prompt="second prompt")

        self.assertEqual(len(self.metrics_port.recorded_ai_interactions), 2)
        first_interaction = self.metrics_port.recorded_ai_interactions[0]
        second_interaction = self.metrics_port.recorded_ai_interactions[1]
        self.assertEqual(first_interaction.input_payload, "first prompt")
        self.assertEqual(first_interaction.output_payload, "first response")
        self.assertEqual(second_interaction.input_payload, "second prompt")
        self.assertEqual(second_interaction.output_payload, "second response")

    def test_generate_reraises_same_exception_instance_on_wrapped_failure(self) -> None:
        original_exception = RuntimeError("backend connection failed")
        failing_generator = FailingLlmGeneratorAdapter(exception=original_exception)
        adapter = self._create_adapter(generator=failing_generator)

        with self.assertRaises(RuntimeError) as error_context:
            adapter.generate(prompt="failing prompt")

        self.assertIs(error_context.exception, original_exception)

    def test_generate_records_error_interaction_on_wrapped_failure(self) -> None:
        original_exception = ValueError("invalid input parameters")
        failing_generator = FailingLlmGeneratorAdapter(exception=original_exception)
        adapter = self._create_adapter(generator=failing_generator)

        with self.assertRaises(ValueError):
            adapter.generate(prompt="failing prompt")

        self.assertEqual(len(self.metrics_port.recorded_ai_interactions), 1)
        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertEqual(recorded_interaction.analysis_id, "analysis-test-identifier")
        self.assertEqual(recorded_interaction.provider, self.provider)
        self.assertEqual(recorded_interaction.purpose, self.purpose)
        self.assertEqual(recorded_interaction.model_name, self.model_name)
        self.assertEqual(recorded_interaction.input_payload, "failing prompt")
        self.assertEqual(
            recorded_interaction.output_payload, "ValueError: invalid input parameters"
        )
        self.assertEqual(recorded_interaction.status, ExecutionStatus.ERROR)
        self.assertIsInstance(recorded_interaction.duration_ms, float)
        self.assertGreaterEqual(recorded_interaction.duration_ms, 0.0)

    def test_generate_records_under_unassigned_when_context_has_no_analysis_id(self) -> None:
        self.context_port.clear_analysis_id()
        wrapped_generator = FakeLlmGeneratorAdapter(["response without context"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="unassigned prompt")

        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertEqual(recorded_interaction.analysis_id, "unassigned")
        self.assertEqual(recorded_interaction.input_payload, "unassigned prompt")
        self.assertEqual(recorded_interaction.output_payload, "response without context")
        self.assertEqual(recorded_interaction.status, ExecutionStatus.SUCCESS)

    def test_generate_records_no_lifecycle_events_other_than_ai_interactions(self) -> None:
        wrapped_generator = FakeLlmGeneratorAdapter(["response"])
        adapter = self._create_adapter(generator=wrapped_generator)

        adapter.generate(prompt="sample prompt")

        self.assertEqual(len(self.metrics_port.recorded_starts), 0)
        self.assertEqual(len(self.metrics_port.recorded_stage_durations), 0)
        self.assertEqual(len(self.metrics_port.recorded_completions), 0)

    def test_generate_records_unicode_and_multiline_prompt_and_response_verbatim(self) -> None:
        multiline_prompt = (
            "Análisis lingüístico:\n"
            "«El ñandú corrió velozmente por la llanura.»\n"
            "¿Detecta alguna inconsistencia tipográfica? 🚀"
        )
        multiline_response = (
            "Resultado del análisis:\n"
            "1. Sin faltas detectadas en «ñandú».\n"
            "2. Comillas angulares utilizadas correctamente."
        )
        wrapped_generator = FakeLlmGeneratorAdapter([multiline_response])
        adapter = self._create_adapter(generator=wrapped_generator)

        response = adapter.generate(prompt=multiline_prompt)

        self.assertEqual(response, multiline_response)
        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertEqual(recorded_interaction.input_payload, multiline_prompt)
        self.assertEqual(recorded_interaction.output_payload, multiline_response)

    def test_generate_records_redacted_payloads_in_prod_mode_on_success(self) -> None:
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        prompt = "Sensible manuscript text to analyze"
        raw_response = "Generated analysis with confidential data"
        wrapped_generator = FakeLlmGeneratorAdapter([raw_response])
        adapter = self._create_adapter(generator=wrapped_generator, audit_payload_policy=policy)

        response = adapter.generate(prompt=prompt)

        self.assertEqual(response, raw_response)
        self.assertEqual(len(self.metrics_port.recorded_ai_interactions), 1)
        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertEqual(recorded_interaction.input_payload, policy.apply(prompt))
        self.assertEqual(recorded_interaction.output_payload, policy.apply(raw_response))
        self.assertEqual(recorded_interaction.provider, self.provider)
        self.assertEqual(recorded_interaction.model_name, self.model_name)
        self.assertEqual(recorded_interaction.purpose, self.purpose)
        self.assertEqual(recorded_interaction.status, ExecutionStatus.SUCCESS)
        self.assertIsInstance(recorded_interaction.duration_ms, float)
        self.assertNotIn("Sensible", recorded_interaction.input_payload)
        self.assertNotIn("manuscript", recorded_interaction.input_payload)
        self.assertNotIn("confidential", recorded_interaction.output_payload)

    def test_generate_records_redacted_exception_message_in_prod_mode_on_failure(
        self,
    ) -> None:
        policy = AuditPayloadPolicy(app_mode=AppMode.PROD)
        sensitive_error_message = (
            "Failure containing manuscript text: PrivateAuthorManuscriptContent"
        )
        original_exception = ValueError(sensitive_error_message)
        failing_generator = FailingLlmGeneratorAdapter(exception=original_exception)
        adapter = self._create_adapter(generator=failing_generator, audit_payload_policy=policy)

        with self.assertRaises(ValueError) as error_context:
            adapter.generate(prompt="failing prompt")

        self.assertIs(error_context.exception, original_exception)
        self.assertEqual(len(self.metrics_port.recorded_ai_interactions), 1)
        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        expected_output_payload = f"ValueError: {policy.apply(sensitive_error_message)}"
        self.assertEqual(recorded_interaction.output_payload, expected_output_payload)
        self.assertEqual(recorded_interaction.input_payload, policy.apply("failing prompt"))
        self.assertNotIn("PrivateAuthorManuscriptContent", recorded_interaction.output_payload)
        self.assertNotIn("PrivateAuthorManuscriptContent", recorded_interaction.input_payload)

    def test_generate_records_full_error_message_in_debug_mode_on_failure(self) -> None:
        policy = AuditPayloadPolicy(app_mode=AppMode.DEBUG)
        error_message = "Failure detail: unredacted error info"
        original_exception = RuntimeError(error_message)
        failing_generator = FailingLlmGeneratorAdapter(exception=original_exception)
        adapter = self._create_adapter(generator=failing_generator, audit_payload_policy=policy)

        with self.assertRaises(RuntimeError):
            adapter.generate(prompt="failing prompt")

        self.assertEqual(len(self.metrics_port.recorded_ai_interactions), 1)
        recorded_interaction = self.metrics_port.recorded_ai_interactions[0]
        self.assertEqual(recorded_interaction.output_payload, f"RuntimeError: {error_message}")
        self.assertEqual(recorded_interaction.input_payload, "failing prompt")
