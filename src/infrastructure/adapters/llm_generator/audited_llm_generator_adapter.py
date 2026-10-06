from logging import getLogger
from time import perf_counter

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.llm_generation_dto import LlmGenerationDTO
from src.domain.enums.ai_provider import AiProvider
from src.domain.enums.ai_purpose import AiPurpose
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.enums.llm_done_reason import LlmDoneReason
from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy
from src.domain.ports.llm_generator_port import LlmGeneratorPort

logger = getLogger(__name__)

_UNASSIGNED_ANALYSIS_ID = "unassigned"
_CAUSE_SEPARATOR = " <- caused by "


class AuditedLlmGeneratorAdapter(LlmGeneratorPort):
    """Decorator adapter for LlmGeneratorPort that measures latency and records interaction telemetry."""

    def __init__(
        self,
        generator: LlmGeneratorPort,
        metrics_port: AnalysisMetricsPort,
        analysis_context_port: AnalysisContextPort,
        provider: AiProvider,
        model_name: str,
        purpose: AiPurpose,
        audit_payload_policy: AuditPayloadPolicy,
    ) -> None:
        self._generator = generator
        self._metrics_port = metrics_port
        self._analysis_context_port = analysis_context_port
        self._provider = provider
        self._model_name = model_name
        self._purpose = purpose
        self._audit_payload_policy = audit_payload_policy

    def generate(self, prompt: str, options: dict | None = None) -> str:
        """Return the generated text for the given prompt while measuring latency and recording telemetry."""
        return self.generate_with_usage(prompt=prompt, options=options).text

    def generate_with_usage(self, prompt: str, options: dict | None = None) -> LlmGenerationDTO:
        """Return the generated text and usage metadata while measuring latency and recording telemetry."""
        analysis_id = self._analysis_context_port.get_analysis_id()
        if analysis_id is None:
            analysis_id = _UNASSIGNED_ANALYSIS_ID

        start_time = perf_counter()
        try:
            generation_result = self._generator.generate_with_usage(prompt=prompt, options=options)
        except Exception as exception:
            duration_ms = (perf_counter() - start_time) * 1000
            self._record_interaction(
                analysis_id=analysis_id,
                prompt=self._audit_payload_policy.apply(prompt),
                output_payload=self._describe_exception(exception),
                duration_ms=duration_ms,
                status=ExecutionStatus.ERROR,
                prompt_tokens=None,
                completion_tokens=None,
                done_reason=None,
            )
            raise

        duration_ms = (perf_counter() - start_time) * 1000
        self._record_interaction(
            analysis_id=analysis_id,
            prompt=self._audit_payload_policy.apply(prompt),
            output_payload=self._audit_payload_policy.apply(generation_result.text),
            duration_ms=duration_ms,
            status=ExecutionStatus.SUCCESS,
            prompt_tokens=generation_result.prompt_tokens,
            completion_tokens=generation_result.completion_tokens,
            done_reason=generation_result.done_reason,
        )
        if generation_result.done_reason == LlmDoneReason.LENGTH.value:
            logger.warning(
                "Language model response truncated by the token limit (purpose=%s, model=%s, prompt_tokens=%s, completion_tokens=%s)",
                self._purpose.value,
                self._model_name,
                generation_result.prompt_tokens,
                generation_result.completion_tokens,
            )
        return generation_result

    def _record_interaction(
        self,
        analysis_id: str,
        prompt: str,
        output_payload: str,
        duration_ms: float,
        status: ExecutionStatus,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        done_reason: str | None = None,
    ) -> None:
        interaction = AiInteractionDTO(
            analysis_id=analysis_id,
            provider=self._provider,
            purpose=self._purpose,
            model_name=self._model_name,
            input_payload=prompt,
            output_payload=output_payload,
            duration_ms=duration_ms,
            status=status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            done_reason=done_reason,
        )
        self._metrics_port.record_ai_interaction(ai_interaction=interaction)

    def _describe_exception(self, exception: BaseException) -> str:
        visited_exception_identifiers: set[int] = set()
        descriptions: list[str] = []
        current_exception: BaseException | None = exception
        while current_exception is not None:
            exception_identifier = id(current_exception)
            if exception_identifier in visited_exception_identifiers:
                break
            visited_exception_identifiers.add(exception_identifier)
            description = (
                f"{type(current_exception).__name__}: "
                f"{self._audit_payload_policy.apply(str(current_exception))}"
            )
            descriptions.append(description)
            current_exception = current_exception.__cause__
        return _CAUSE_SEPARATOR.join(descriptions)
