from contextlib import closing
from pathlib import Path
from sqlite3 import IntegrityError, connect
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.domain.dtos.ai_interaction_dto import AiInteractionDTO
from src.domain.dtos.analysis_completion_dto import AnalysisCompletionDTO
from src.domain.dtos.analysis_start_dto import AnalysisStartDTO
from src.domain.dtos.stage_duration_dto import StageDurationDTO
from src.domain.metrics.analysis_metrics_port import AnalysisMetricsPort
from src.infrastructure.adapters.metrics.sqlite_analysis_metrics_adapter import (
    SqliteAnalysisMetricsAdapter,
)


class TestSqliteAnalysisMetricsAdapter(TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_directory = Path(self.temporary_directory.name) / "nested_metrics_directory"
        self.database_path = str(self.database_directory / "metrics.db")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_is_instance_of_analysis_metrics_port(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        self.assertIsInstance(adapter, AnalysisMetricsPort)

    def test_creates_database_file_and_missing_parent_folders(self) -> None:
        self.assertFalse(self.database_directory.exists())
        SqliteAnalysisMetricsAdapter(self.database_path)
        self.assertTrue(self.database_directory.exists())
        self.assertTrue(Path(self.database_path).is_file())

    def test_journal_mode_is_configured_to_wal(self) -> None:
        SqliteAnalysisMetricsAdapter(self.database_path)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
            self.assertEqual(journal_mode.lower(), "wal")

    def test_creates_analyses_stage_durations_and_ai_interactions_tables(self) -> None:
        SqliteAnalysisMetricsAdapter(self.database_path)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = {row[0] for row in cursor.fetchall()}
            self.assertIn("analyses", table_names)
            self.assertIn("stage_durations", table_names)
            self.assertIn("ai_interactions", table_names)

            cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index';")
            index_rows = cursor.fetchall()
            indexed_tables = {row[1] for row in index_rows}
            self.assertIn("stage_durations", indexed_tables)
            self.assertIn("ai_interactions", indexed_tables)

    def test_second_adapter_initialization_on_same_file_is_idempotent_and_preserves_data(
        self,
    ) -> None:
        first_adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        first_adapter.record_analysis_start(
            AnalysisStartDTO(
                analysis_id="analysis-idempotent-1",
                document_name="document-1.pdf",
            )
        )
        SqliteAnalysisMetricsAdapter(self.database_path)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT analysis_id, document_name FROM analyses;")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "analysis-idempotent-1")
            self.assertEqual(rows[0][1], "document-1.pdf")

    def test_record_analysis_start_inserts_row_with_running_status_and_iso_timestamp(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        start_dto = AnalysisStartDTO(
            analysis_id="analysis-start-1",
            document_name="editorial_article.docx",
        )
        adapter.record_analysis_start(start_dto)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT analysis_id, document_name, status, started_at, completed_at FROM analyses WHERE analysis_id = ?;",
                ("analysis-start-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "analysis-start-1")
            self.assertEqual(row[1], "editorial_article.docx")
            self.assertEqual(row[2], "running")
            self.assertTrue(len(row[3]) > 0)
            self.assertIn("T", row[3])
            self.assertIsNone(row[4])

    def test_duplicate_analysis_start_raises_sqlite_integrity_error(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        start_dto = AnalysisStartDTO(
            analysis_id="duplicate-analysis-id",
            document_name="first_run.docx",
        )
        adapter.record_analysis_start(start_dto)
        with self.assertRaises(IntegrityError):
            adapter.record_analysis_start(start_dto)

    def test_record_analysis_completion_updates_existing_row_and_preserves_started_at(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        start_dto = AnalysisStartDTO(
            analysis_id="analysis-update-1",
            document_name="original_name.docx",
        )
        adapter.record_analysis_start(start_dto)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT started_at FROM analyses WHERE analysis_id = ?;", ("analysis-update-1",)
            )
            original_started_at = cursor.fetchone()[0]

        completion_dto = AnalysisCompletionDTO(
            analysis_id="analysis-update-1",
            document_name="updated_name.docx",
            word_count=1500,
            char_count=9800,
            article_type="investigative_journalism",
            verdict="approved",
            total_duration_ms=4520.5,
            status="completed",
        )
        adapter.record_analysis_completion(completion_dto)

        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT analysis_id, document_name, status, started_at, completed_at, word_count, char_count, article_type, verdict, total_duration_ms FROM analyses WHERE analysis_id = ?;",
                ("analysis-update-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "analysis-update-1")
            self.assertEqual(row[1], "updated_name.docx")
            self.assertEqual(row[2], "completed")
            self.assertEqual(row[3], original_started_at)
            self.assertIsNotNone(row[4])
            self.assertTrue(len(row[4]) > 0)
            self.assertEqual(row[5], 1500)
            self.assertEqual(row[6], 9800)
            self.assertEqual(row[7], "investigative_journalism")
            self.assertEqual(row[8], "approved")
            self.assertEqual(row[9], 4520.5)

    def test_record_analysis_completion_without_prior_start_inserts_new_row(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        completion_dto = AnalysisCompletionDTO(
            analysis_id="analysis-standalone-1",
            document_name="standalone_article.docx",
            word_count=850,
            char_count=5200,
            article_type="opinion_column",
            verdict="revision_required",
            total_duration_ms=2100.0,
            status="completed",
        )
        adapter.record_analysis_completion(completion_dto)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT analysis_id, document_name, status, started_at, completed_at, word_count, char_count, article_type, verdict, total_duration_ms FROM analyses WHERE analysis_id = ?;",
                ("analysis-standalone-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "analysis-standalone-1")
            self.assertEqual(row[1], "standalone_article.docx")
            self.assertEqual(row[2], "completed")
            self.assertIsNotNone(row[3])
            self.assertTrue(len(row[3]) > 0)
            self.assertEqual(row[3], row[4])
            self.assertEqual(row[5], 850)
            self.assertEqual(row[6], 5200)
            self.assertEqual(row[7], "opinion_column")
            self.assertEqual(row[8], "revision_required")
            self.assertEqual(row[9], 2100.0)

    def test_record_stage_duration_stores_row(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        stage_dto = StageDurationDTO(
            analysis_id="analysis-stage-1",
            stage_name="orthographic_inspection",
            duration_ms=134.8,
        )
        adapter.record_stage_duration(stage_dto)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT analysis_id, stage_name, duration_ms, recorded_at FROM stage_durations WHERE analysis_id = ?;",
                ("analysis-stage-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "analysis-stage-1")
            self.assertEqual(row[1], "orthographic_inspection")
            self.assertEqual(row[2], 134.8)
            self.assertTrue(len(row[3]) > 0)
            self.assertIn("T", row[3])

    def test_record_ai_interaction_stores_verbatim_payloads_with_unicode_multiline_and_large_content(
        self,
    ) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        large_unicode_input = (
            "Texto en español con acentos: áéíóú, ñ, ü y emojis: 🔍📝.\nSegunda línea.\n"
            + ("X" * 100000)
        )
        multiline_output = '{\n  "verdict": "valid",\n  "details": "Línea con puntuación y caracteres especiales"\n}'
        interaction_dto = AiInteractionDTO(
            analysis_id="analysis-ai-1",
            provider="ollama",
            purpose="style_analysis",
            model_name="llama3.1:8b",
            input_payload=large_unicode_input,
            output_payload=multiline_output,
            duration_ms=1520.4,
            status="success",
        )
        adapter.record_ai_interaction(interaction_dto)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT analysis_id, provider, purpose, model_name, input_payload, output_payload, duration_ms, status, recorded_at FROM ai_interactions WHERE analysis_id = ?;",
                ("analysis-ai-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "analysis-ai-1")
            self.assertEqual(row[1], "ollama")
            self.assertEqual(row[2], "style_analysis")
            self.assertEqual(row[3], "llama3.1:8b")
            self.assertEqual(row[4], large_unicode_input)
            self.assertEqual(row[5], multiline_output)
            self.assertEqual(row[6], 1520.4)
            self.assertEqual(row[7], "success")
            self.assertTrue(len(row[8]) > 0)

    def test_record_ai_interaction_with_sql_injection_payload_is_parameterized_and_table_survives(
        self,
    ) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        sql_injection_payload = "'); DROP TABLE analyses; --"
        interaction_dto = AiInteractionDTO(
            analysis_id="analysis-sql-injection-1",
            provider="laya",
            purpose="decision_gate",
            model_name="laya-ensemble-v1",
            input_payload=sql_injection_payload,
            output_payload=sql_injection_payload,
            duration_ms=45.2,
            status="success",
        )
        adapter.record_ai_interaction(interaction_dto)
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analyses';")
            self.assertIsNotNone(cursor.fetchone())
            cursor.execute(
                "SELECT input_payload, output_payload FROM ai_interactions WHERE analysis_id = ?;",
                ("analysis-sql-injection-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], sql_injection_payload)
            self.assertEqual(row[1], sql_injection_payload)

    def test_multiple_ai_interactions_for_same_analysis_are_stored_in_insertion_order(self) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        for index in range(5):
            adapter.record_ai_interaction(
                AiInteractionDTO(
                    analysis_id="analysis-multiple-interactions",
                    provider="ollama",
                    purpose=f"stage_step_{index}",
                    model_name="llama3.1:8b",
                    input_payload=f"input_{index}",
                    output_payload=f"output_{index}",
                    duration_ms=float(index * 10),
                    status="success",
                )
            )
        with closing(connect(self.database_path)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT purpose, input_payload, duration_ms FROM ai_interactions WHERE analysis_id = ? ORDER BY id ASC;",
                ("analysis-multiple-interactions",),
            )
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 5)
            for index, row in enumerate(rows):
                self.assertEqual(row[0], f"stage_step_{index}")
                self.assertEqual(row[1], f"input_{index}")
                self.assertEqual(row[2], float(index * 10))

    def test_data_written_by_one_adapter_instance_is_immediately_visible_in_fresh_connection(
        self,
    ) -> None:
        adapter = SqliteAnalysisMetricsAdapter(self.database_path)
        adapter.record_analysis_start(
            AnalysisStartDTO(
                analysis_id="analysis-isolation-1",
                document_name="committed_check.txt",
            )
        )
        with closing(connect(self.database_path)) as fresh_connection:
            cursor = fresh_connection.cursor()
            cursor.execute(
                "SELECT document_name, status FROM analyses WHERE analysis_id = ?;",
                ("analysis-isolation-1",),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "committed_check.txt")
            self.assertEqual(row[1], "running")
