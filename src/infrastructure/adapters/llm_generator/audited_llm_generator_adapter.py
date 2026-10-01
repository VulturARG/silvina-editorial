from time import perf_counter

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.metrics.analysis_context_port import AnalysisContextPort
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort
from src.domain.metrics.audit_payload_policy import AuditPayloadPolicy
from src.domain.ports.llm_generator_port import LlmGeneratorPort

_UNASSIGNED_ANALYSIS_ID = "unassigned"


class AuditedLlmGeneratorAdapter(LlmGeneratorPort):
    """Decorator adapter for LlmGeneratorPort that measures latency and records interaction telemetry."""

    def __init__(
        self,
        generator: LlmGeneratorPort,
        metrics_port: AnalysisMetricsPort,
        analysis_context_port: AnalysisContextPort,
        provider: str,
        model_name: str,
        purpose: str,
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
        analysis_id = self._analysis_context_port.get_analysis_id()
        if analysis_id is None:
            analysis_id = _UNASSIGNED_ANALYSIS_ID

        start_time = perf_counter()
        try:
            response = self._generator.generate(prompt=prompt, options=options)
        except Exception as exc:
            duration_ms = (perf_counter() - start_time) * 1000
            self._record_interaction(
                analysis_id=analysis_id,
                prompt=self._audit_payload_policy.apply(prompt),
                output_payload=f"{type(exc).__name__}: {self._audit_payload_policy.apply(str(exc))}",
                duration_ms=duration_ms,
                status="error",
            )
            raise

        duration_ms = (perf_counter() - start_time) * 1000
        self._record_interaction(
            analysis_id=analysis_id,
            prompt=self._audit_payload_policy.apply(prompt),
            output_payload=self._audit_payload_policy.apply(response),
            duration_ms=duration_ms,
            status="success",
        )
        return response

    def _record_interaction(
        self,
        analysis_id: str,
        prompt: str,
        output_payload: str,
        duration_ms: float,
        status: str,
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
        )
        self._metrics_port.record_ai_interaction(ai_interaction=interaction)
