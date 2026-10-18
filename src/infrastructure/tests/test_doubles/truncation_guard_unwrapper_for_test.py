from src.domain.ports.llm_generator_port import LlmGeneratorPort
from src.infrastructure.adapters.llm_generator.audited_llm_generator_adapter import (
    AuditedLlmGeneratorAdapter,
)
from src.infrastructure.adapters.llm_generator.truncation_guard_llm_generator_adapter import (
    TruncationGuardLlmGeneratorAdapter,
)


class TruncationGuardUnwrapperForTest:
    """Reaches the audited generator that a wired truncation guard decorates."""

    @staticmethod
    def audited_generator(guard: LlmGeneratorPort) -> AuditedLlmGeneratorAdapter:
        """Return the audited adapter decorated by the given truncation guard."""
        assert isinstance(guard, TruncationGuardLlmGeneratorAdapter)
        assert isinstance(guard._generator, AuditedLlmGeneratorAdapter)
        return guard._generator
