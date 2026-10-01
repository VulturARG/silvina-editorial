from contextlib import closing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from sqlite3 import connect

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.enums.execution_status import ExecutionStatus
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort


class SqliteAnalysisMetricsAdapter(AnalysisMetricsPort):
    """Persists analysis telemetry and metrics into a local SQLite database."""

    def __init__(self, database_path: str) -> None:
        """Initialize the SQLite metrics adapter and ensure the schema exists."""
        self._database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with closing(connect(self._database_path)) as connection:
            connection.execute("PRAGMA journal_mode = WAL;")
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analyses (
                        analysis_id TEXT PRIMARY KEY,
                        document_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        completed_at TEXT,
                        word_count INTEGER,
                        char_count INTEGER,
                        article_type TEXT,
                        verdict TEXT,
                        total_duration_ms REAL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stage_durations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL,
                        stage_name TEXT NOT NULL,
                        duration_ms REAL NOT NULL,
                        recorded_at TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS index_stage_durations_analysis_id ON stage_durations(analysis_id);
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ai_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        model_name TEXT NOT NULL,
                        input_payload TEXT NOT NULL,
                        output_payload TEXT NOT NULL,
                        duration_ms REAL NOT NULL,
                        status TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS index_ai_interactions_analysis_id ON ai_interactions(analysis_id);
                    """
                )

    def record_analysis_start(self, start_data: AnalysisStartDTO) -> None:
        """Record the beginning of a document analysis."""
        started_at = datetime.now(timezone.utc).isoformat()
        with closing(connect(self._database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO analyses (
                        analysis_id,
                        document_name,
                        status,
                        started_at
                    ) VALUES (?, ?, ?, ?);
                    """,
                    (
                        start_data.analysis_id,
                        start_data.document_name,
                        ExecutionStatus.RUNNING.value,
                        started_at,
                    ),
                )

    def record_stage_duration(self, stage_duration: StageDurationDTO) -> None:
        """Record the execution duration of an analysis stage in milliseconds."""
        recorded_at = datetime.now(timezone.utc).isoformat()
        with closing(connect(self._database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO stage_durations (
                        analysis_id,
                        stage_name,
                        duration_ms,
                        recorded_at
                    ) VALUES (?, ?, ?, ?);
                    """,
                    (
                        stage_duration.analysis_id,
                        stage_duration.stage_name,
                        stage_duration.duration_ms,
                        recorded_at,
                    ),
                )

    def record_ai_interaction(self, ai_interaction: AiInteractionDTO) -> None:
        """Record telemetry of an external AI interaction."""
        recorded_at = datetime.now(timezone.utc).isoformat()
        with closing(connect(self._database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO ai_interactions (
                        analysis_id,
                        provider,
                        purpose,
                        model_name,
                        input_payload,
                        output_payload,
                        duration_ms,
                        status,
                        recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        ai_interaction.analysis_id,
                        ai_interaction.provider,
                        ai_interaction.purpose,
                        ai_interaction.model_name,
                        ai_interaction.input_payload,
                        ai_interaction.output_payload,
                        ai_interaction.duration_ms,
                        self._enum_value(ai_interaction.status),
                        recorded_at,
                    ),
                )

    def record_analysis_completion(self, completion_data: AnalysisCompletionDTO) -> None:
        """Record the final summary and outcome of a document analysis."""
        completed_at = datetime.now(timezone.utc).isoformat()
        with closing(connect(self._database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO analyses (
                        analysis_id,
                        document_name,
                        status,
                        started_at,
                        completed_at,
                        word_count,
                        char_count,
                        article_type,
                        verdict,
                        total_duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(analysis_id) DO UPDATE SET
                        document_name = excluded.document_name,
                        status = excluded.status,
                        completed_at = excluded.completed_at,
                        word_count = excluded.word_count,
                        char_count = excluded.char_count,
                        article_type = excluded.article_type,
                        verdict = excluded.verdict,
                        total_duration_ms = excluded.total_duration_ms;
                    """,
                    (
                        completion_data.analysis_id,
                        completion_data.document_name,
                        self._enum_value(completion_data.status),
                        completed_at,
                        completed_at,
                        completion_data.word_count,
                        completion_data.char_count,
                        self._enum_value(completion_data.article_type),
                        self._enum_value(completion_data.verdict),
                        completion_data.total_duration_ms,
                    ),
                )

    @staticmethod
    def _enum_value(member: Enum | None) -> str | None:
        if member is None:
            return None
        return member.value
