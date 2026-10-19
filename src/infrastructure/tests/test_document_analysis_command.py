from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock

from src.application.analyze_document_use_case import AnalyzeDocumentUseCase
from src.application.ensure_language_model_server_use_case import (
    EnsureLanguageModelServerUseCase,
)
from src.application.export_report_use_case import ExportReportUseCase
from src.application.release_language_model_server_use_case import (
    ReleaseLanguageModelServerUseCase,
)
from src.application.warm_up_language_model_use_case import WarmUpLanguageModelUseCase
from src.domain.dtos.prompt_source_dto import PromptSourceDTO
from src.domain.exceptions.language_model_errors import (
    LanguageModelError,
    LanguageModelLoadFailed,
    LanguageModelNotFound,
    LanguageModelServerStartFailed,
    LanguageModelUnavailable,
)
from src.infrastructure.cli.cli_analysis_services import CliAnalysisServices
from src.infrastructure.cli.command_line_arguments import CommandLineArguments
from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer
from src.infrastructure.cli.document_analysis_command import DocumentAnalysisCommand
from src.infrastructure.cli.document_name_prompter import DocumentNamePrompter
from src.infrastructure.cli.report_file_paths_builder import ReportFilePathsBuilder
from src.infrastructure.cli.source_document_locator import SourceDocumentLocator
from src.infrastructure.cli.windows_file_name_sanitizer import WindowsFileNameSanitizer


class TestDocumentAnalysisCommand(TestCase):
    MODEL_NAME = "gemma-test"
    DOCUMENT_NAME = "tesis.docx"
    DEFAULT_PROMPT_SOURCE = PromptSourceDTO(
        base_label=PromptSourceDTO.DEFAULT_BASE_LABEL, replaced_prompt_names=()
    )

    def setUp(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self._input_directory = Path(temporary_directory.name)
        self._document_path = self._input_directory / self.DOCUMENT_NAME
        self._document_path.write_bytes(b"docx placeholder")
        self._printed_lines: list[str] = []
        self._answer_function = MagicMock(return_value=self.DOCUMENT_NAME)
        self._report = MagicMock(name="report")
        self._ensure_language_model_server_use_case = MagicMock(
            spec=EnsureLanguageModelServerUseCase
        )
        self._release_language_model_server_use_case = MagicMock(
            spec=ReleaseLanguageModelServerUseCase
        )
        self._warm_up_language_model_use_case = MagicMock(spec=WarmUpLanguageModelUseCase)
        self._analyze_document_use_case = MagicMock(spec=AnalyzeDocumentUseCase)
        self._analyze_document_use_case.execute.return_value = self._report
        self._word_report_use_case = self._successful_export_use_case()
        self._json_report_use_case = self._successful_export_use_case()
        self._html_report_use_case = self._successful_export_use_case()
        self._services_factory = MagicMock(return_value=self._build_services(self.MODEL_NAME))

    def test_returns_zero_when_analysis_and_exports_succeed(self):
        status = self._run(self._arguments())

        self.assertEqual(status, 0)

    def test_prints_start_and_finish_of_each_step_then_the_generated_paths(self):
        self._run(self._arguments())

        base_directory = self._expected_directory()
        self.assertEqual(
            self._printed_lines,
            [
                "⏳ Validando el documento...",
                "✅ Validando el documento: terminado",
                "⏳ Preparando la configuración y los casos de uso...",
                "✅ Preparando la configuración y los casos de uso: terminado",
                "⏳ Calculando las rutas de los informes...",
                "✅ Calculando las rutas de los informes: terminado",
                "⏳ Verificando el servidor del modelo de lenguaje...",
                "✅ Verificando el servidor del modelo de lenguaje: terminado",
                "⏳ Precargando el modelo de lenguaje...",
                "✅ Precargando el modelo de lenguaje: terminado",
                "⏳ Analizando el documento...",
                "✅ Analizando el documento: terminado",
                "⏳ Creando el directorio de salida...",
                "✅ Creando el directorio de salida: terminado",
                "⏳ Guardando el informe Word...",
                "✅ Guardando el informe Word: terminado",
                "⏳ Guardando el informe JSON...",
                "✅ Guardando el informe JSON: terminado",
                "⏳ Guardando el informe HTML...",
                "✅ Guardando el informe HTML: terminado",
                "🎉 Ejecución terminada",
                f"   📄 {base_directory / 'tesis_analisis_gemma-test.docx'}",
                f"   📄 {base_directory / 'tesis_analisis_gemma-test.json'}",
                f"   📄 {base_directory / 'tesis_analisis_gemma-test.html'}",
            ],
        )

    def test_creates_default_analysis_directory_next_to_document(self):
        self._run(self._arguments())

        self.assertTrue(self._expected_directory().is_dir())

    def test_logs_prompt_source_description_once_per_run(self):
        prompt_source = PromptSourceDTO(
            base_label="v2", replaced_prompt_names=("alignment_prompt",)
        )
        self._services_factory.return_value = self._build_services(
            self.MODEL_NAME, prompt_source=prompt_source
        )

        with self.assertLogs(level="INFO") as captured_logs:
            self._run(self._arguments())

        prompt_source_lines = [line for line in captured_logs.output if "Prompt source" in line]
        self.assertEqual(
            prompt_source_lines,
            [
                "INFO:src.infrastructure.cli.document_analysis_command:"
                "Prompt source: v2 + alignment_prompt"
            ],
        )

    def test_logs_default_prompt_source_when_no_custom_prompts_are_used(self):
        with self.assertLogs(level="INFO") as captured_logs:
            self._run(self._arguments())

        self.assertIn(
            "INFO:src.infrastructure.cli.document_analysis_command:Prompt source: default",
            captured_logs.output,
        )

    def test_prompt_source_is_not_printed_to_console(self):
        self._run(self._arguments())

        self.assertNotIn("Prompt source", "".join(self._printed_lines))

    def test_exports_word_json_and_html_reports_into_output_directory(self):
        self._run(self._arguments())

        base_directory = self._expected_directory()
        self._word_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(base_directory / "tesis_analisis_gemma-test.docx"),
        )
        self._json_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(base_directory / "tesis_analisis_gemma-test.json"),
        )
        self._html_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(base_directory / "tesis_analisis_gemma-test.html"),
        )

    def test_exports_reports_with_prompt_source_suffix_in_their_names(self):
        prompt_source = PromptSourceDTO(
            base_label="v2",
            replaced_prompt_names=("alignment_prompt",),
            uses_custom_prompts_root=True,
        )
        self._services_factory.return_value = self._build_services(
            self.MODEL_NAME, prompt_source=prompt_source
        )

        self._run(self._arguments())

        base_directory = self._expected_directory()
        self._word_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(base_directory / "tesis_analisis_gemma-test_v2+alignment_prompt.docx"),
        )
        self._json_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(base_directory / "tesis_analisis_gemma-test_v2+alignment_prompt.json"),
        )
        self._html_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(base_directory / "tesis_analisis_gemma-test_v2+alignment_prompt.html"),
        )

    def test_default_prompt_source_keeps_report_names_without_suffix(self):
        self._services_factory.return_value = self._build_services(
            self.MODEL_NAME, prompt_source=self.DEFAULT_PROMPT_SOURCE
        )

        self._run(self._arguments())

        self._word_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(self._expected_directory() / "tesis_analisis_gemma-test.docx"),
        )

    def test_honors_explicit_output_directory_and_creates_it_with_parents(self):
        output_directory = self._input_directory / "salida" / "nueva"

        status = self._run(self._arguments(output_directory=output_directory))

        self.assertEqual(status, 0)
        self.assertTrue(output_directory.is_dir())
        self.assertFalse(self._expected_directory().exists())
        self._word_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(output_directory / "tesis_analisis_gemma-test.docx"),
        )

    def test_asks_for_document_name_when_it_is_missing(self):
        arguments = CommandLineArguments(input_directory=self._input_directory)

        status = self._run(arguments)

        self.assertEqual(status, 0)
        self._answer_function.assert_called_once_with(DocumentNamePrompter.PROMPT_TEXT)
        self.assertIn("⏳ Solicitando el nombre del documento...", self._printed_lines)
        self.assertIn("✅ Solicitando el nombre del documento: terminado", self._printed_lines)

    def test_does_not_ask_for_document_name_when_it_is_given(self):
        self._run(self._arguments())

        self._answer_function.assert_not_called()
        self.assertNotIn("⏳ Solicitando el nombre del documento...", self._printed_lines)

    def test_analyzes_document_with_file_name_and_path_like_the_web(self):
        self._run(self._arguments())

        self._analyze_document_use_case.execute.assert_called_once_with(
            document_path=str(self._document_path.resolve()),
            document_name=self.DOCUMENT_NAME,
        )

    def test_passes_environment_overrides_of_arguments_to_services_factory(self):
        arguments = CommandLineArguments(
            document_name=self.DOCUMENT_NAME,
            input_directory=self._input_directory,
            ollama_model_name="modelo-x",
            use_external_llm=False,
            app_mode="DEBUG",
        )

        self._run(arguments)

        self._services_factory.assert_called_once_with(
            {
                "OLLAMA_MODEL_NAME": "modelo-x",
                "USE_EXTERNAL_LLM": "false",
                "LLM_PROVIDER": None,
                "EXTERNAL_LLM_MODEL_NAME": None,
                "APP_MODE": "DEBUG",
            },
            arguments.prompt_file_overrides(),
            None,
        )

    def test_passes_prompt_file_overrides_to_services_factory(self):
        prompt_directory = self._input_directory / "prompts"
        prompt_directory.mkdir()
        (prompt_directory / "s4_s5_s6_signal_prompt.txt").write_text("signal", encoding="utf-8")
        arguments = CommandLineArguments(
            document_name=self.DOCUMENT_NAME,
            input_directory=self._input_directory,
            s4_s5_s6_signal_prompt=prompt_directory,
        )

        self._run(arguments)

        self._services_factory.assert_called_once_with(
            arguments.environment_overrides(),
            arguments.prompt_file_overrides(),
            None,
        )

    def test_passes_prompts_directory_to_services_factory(self):
        prompts_directory = self._input_directory / "prompts"
        arguments = CommandLineArguments(
            document_name=self.DOCUMENT_NAME,
            input_directory=self._input_directory,
            prompts_directory=prompts_directory,
        )

        self._run(arguments)

        self._services_factory.assert_called_once_with(
            arguments.environment_overrides(),
            arguments.prompt_file_overrides(),
            prompts_directory,
        )

    def test_model_name_from_services_appears_sanitized_in_report_file_names(self):
        self._services_factory.return_value = self._build_services(model_name="modelo:7b")

        self._run(self._arguments())

        self._word_report_use_case.execute.assert_called_once_with(
            report_input=self._report,
            output_path=str(self._expected_directory() / "tesis_analisis_modelo_7b.docx"),
        )

    def test_missing_document_returns_two_with_detail_and_skips_analysis(self):
        status = self._run(self._arguments(document_name="no_existe.docx"))

        missing_path = (self._input_directory / "no_existe.docx").resolve()
        self.assertEqual(status, 2)
        self.assertEqual(self._printed_lines[-1], f"❌ El documento no existe: {missing_path}")
        self._services_factory.assert_not_called()
        self._analyze_document_use_case.execute.assert_not_called()

    def test_document_that_is_not_docx_returns_two_with_word_message(self):
        legacy_document_path = self._input_directory / "notas.doc"
        legacy_document_path.write_bytes(b"legacy placeholder")

        status = self._run(self._arguments(document_name="notas.doc"))

        self.assertEqual(status, 2)
        self.assertEqual(
            self._printed_lines[-1],
            f"❌ El documento debe ser un archivo Word (.docx): {legacy_document_path.resolve()}",
        )
        self._analyze_document_use_case.execute.assert_not_called()

    def test_services_factory_error_returns_one_with_its_message(self):
        self._services_factory.side_effect = ValueError("El valor de USE_EXTERNAL_LLM no es válido")

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], "❌ El valor de USE_EXTERNAL_LLM no es válido")
        self._analyze_document_use_case.execute.assert_not_called()
        self.assertFalse(self._expected_directory().exists())

    def test_language_model_unavailable_returns_one_with_clean_message(self):
        self._assert_analysis_error_is_reported_cleanly(LanguageModelUnavailable)

    def test_language_model_not_found_returns_one_with_clean_message(self):
        self._assert_analysis_error_is_reported_cleanly(LanguageModelNotFound)

    def test_language_model_load_failed_returns_one_with_clean_message(self):
        self._assert_analysis_error_is_reported_cleanly(LanguageModelLoadFailed)

    def test_checks_server_then_warms_up_then_analyzes(self):
        execution_order: list[str] = []
        self._ensure_language_model_server_use_case.execute.side_effect = lambda: (
            execution_order.append("server_check")
        )
        self._warm_up_language_model_use_case.execute.side_effect = lambda: execution_order.append(
            "warm_up"
        )
        self._analyze_document_use_case.execute.side_effect = lambda **_kwargs: (
            execution_order.append("analyze"),
            self._report,
        )[1]

        self._run(self._arguments())

        self._ensure_language_model_server_use_case.execute.assert_called_once_with()
        self._warm_up_language_model_use_case.execute.assert_called_once_with()
        self.assertEqual(execution_order, ["server_check", "warm_up", "analyze"])
        self.assertLess(
            self._printed_lines.index("✅ Calculando las rutas de los informes: terminado"),
            self._printed_lines.index("⏳ Verificando el servidor del modelo de lenguaje..."),
        )
        self.assertLess(
            self._printed_lines.index(
                "✅ Verificando el servidor del modelo de lenguaje: terminado"
            ),
            self._printed_lines.index("⏳ Precargando el modelo de lenguaje..."),
        )
        self.assertLess(
            self._printed_lines.index("✅ Precargando el modelo de lenguaje: terminado"),
            self._printed_lines.index("⏳ Analizando el documento..."),
        )

    def test_ensure_language_model_server_start_failed_returns_one_with_clean_message(self):
        self._ensure_language_model_server_use_case.execute.side_effect = (
            LanguageModelServerStartFailed()
        )

        status = self._run(self._arguments())

        printed_text = "\n".join(self._printed_lines)
        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], f"❌ {LanguageModelServerStartFailed.MESSAGE}")
        self.assertNotIn("Error inesperado", printed_text)
        self.assertNotIn(
            "✅ Verificando el servidor del modelo de lenguaje: terminado",
            self._printed_lines,
        )
        self._warm_up_language_model_use_case.execute.assert_not_called()
        self._analyze_document_use_case.execute.assert_not_called()
        self._word_report_use_case.execute.assert_not_called()
        self._json_report_use_case.execute.assert_not_called()
        self._html_report_use_case.execute.assert_not_called()
        self.assertFalse(self._expected_directory().exists())

    def test_warms_up_language_model_after_computing_paths_and_before_analysis(self):
        execution_order: list[str] = []
        self._warm_up_language_model_use_case.execute.side_effect = lambda: execution_order.append(
            "warm_up"
        )
        self._analyze_document_use_case.execute.side_effect = lambda **_kwargs: (
            execution_order.append("analyze"),
            self._report,
        )[1]

        self._run(self._arguments())

        self._warm_up_language_model_use_case.execute.assert_called_once_with()
        self.assertEqual(execution_order, ["warm_up", "analyze"])
        self.assertLess(
            self._printed_lines.index("✅ Calculando las rutas de los informes: terminado"),
            self._printed_lines.index("⏳ Precargando el modelo de lenguaje..."),
        )
        self.assertLess(
            self._printed_lines.index("✅ Precargando el modelo de lenguaje: terminado"),
            self._printed_lines.index("⏳ Analizando el documento..."),
        )

    def test_warm_up_language_model_unavailable_returns_one_with_clean_message(self):
        self._assert_warm_up_error_is_reported_cleanly(LanguageModelUnavailable)

    def test_warm_up_language_model_not_found_returns_one_with_clean_message(self):
        self._assert_warm_up_error_is_reported_cleanly(LanguageModelNotFound)

    def test_warm_up_language_model_load_failed_returns_one_with_clean_message(self):
        self._assert_warm_up_error_is_reported_cleanly(LanguageModelLoadFailed)

    def test_word_export_returning_false_returns_one_and_skips_other_exports(self):
        self._word_report_use_case.execute.return_value = False

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], "❌ No se pudo guardar el informe Word (DOCX)")
        self._json_report_use_case.execute.assert_not_called()
        self._html_report_use_case.execute.assert_not_called()

    def test_failed_word_export_does_not_announce_its_step_as_finished(self):
        self._word_report_use_case.execute.return_value = False

        self._run(self._arguments())

        self.assertIn("⏳ Guardando el informe Word...", self._printed_lines)
        self.assertNotIn("✅ Guardando el informe Word: terminado", self._printed_lines)

    def test_json_export_returning_false_returns_one_without_html_or_completion(self):
        self._json_report_use_case.execute.return_value = False

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], "❌ No se pudo guardar el informe JSON")
        self._html_report_use_case.execute.assert_not_called()
        self.assertNotIn("🎉 Ejecución terminada", self._printed_lines)

    def test_html_export_returning_false_returns_one_without_completion(self):
        self._html_report_use_case.execute.return_value = False

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], "❌ No se pudo guardar el informe HTML")
        self.assertNotIn("🎉 Ejecución terminada", self._printed_lines)

    def test_blank_document_name_answer_returns_two_with_explicit_message(self):
        self._answer_function.return_value = "   "
        arguments = CommandLineArguments(input_directory=self._input_directory)

        status = self._run(arguments)

        self.assertEqual(status, 2)
        self.assertEqual(self._printed_lines[-1], "❌ No se indicó el nombre del documento")
        self._services_factory.assert_not_called()
        self._analyze_document_use_case.execute.assert_not_called()

    def test_unexpected_error_returns_one_with_generic_prefix(self):
        self._analyze_document_use_case.execute.side_effect = RuntimeError("fallo inesperado")

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], "❌ Error inesperado: fallo inesperado")

    def test_keyboard_interrupt_returns_interrupted_status_with_interruption_message(self):
        self._analyze_document_use_case.execute.side_effect = KeyboardInterrupt()

        status = self._run(self._arguments())

        self.assertEqual(status, DocumentAnalysisCommand.INTERRUPTED_STATUS)
        self.assertEqual(self._printed_lines[-1], "❌ Análisis interrumpido por el usuario")

    def _assert_warm_up_error_is_reported_cleanly(
        self, error_class: type[LanguageModelError]
    ) -> None:
        self._warm_up_language_model_use_case.execute.side_effect = error_class()

        status = self._run(self._arguments())

        printed_text = "\n".join(self._printed_lines)
        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], f"❌ {error_class.MESSAGE}")
        self.assertNotIn("Error inesperado", printed_text)
        self.assertNotIn("✅ Precargando el modelo de lenguaje: terminado", self._printed_lines)
        self._analyze_document_use_case.execute.assert_not_called()
        self._word_report_use_case.execute.assert_not_called()
        self._json_report_use_case.execute.assert_not_called()
        self._html_report_use_case.execute.assert_not_called()
        self.assertFalse(self._expected_directory().exists())

    def _assert_analysis_error_is_reported_cleanly(
        self, error_class: type[LanguageModelError]
    ) -> None:
        self._analyze_document_use_case.execute.side_effect = error_class()

        status = self._run(self._arguments())

        printed_text = "\n".join(self._printed_lines)
        self.assertEqual(status, 1)
        self.assertEqual(self._printed_lines[-1], f"❌ {error_class.MESSAGE}")
        self.assertNotIn("Error inesperado", printed_text)
        self.assertNotIn("Error durante el análisis", printed_text)
        self.assertNotIn("✅ Analizando el documento: terminado", self._printed_lines)
        self._word_report_use_case.execute.assert_not_called()
        self._json_report_use_case.execute.assert_not_called()
        self._html_report_use_case.execute.assert_not_called()
        self.assertFalse(self._expected_directory().exists())

    def _run(self, arguments: CommandLineArguments) -> int:
        command = DocumentAnalysisCommand(
            document_name_prompter=DocumentNamePrompter(input_function=self._answer_function),
            source_document_locator=SourceDocumentLocator(),
            report_file_paths_builder=ReportFilePathsBuilder(
                file_name_sanitizer=WindowsFileNameSanitizer()
            ),
            console_step_announcer=ConsoleStepAnnouncer(write_function=self._printed_lines.append),
            services_factory=self._services_factory,
        )
        return command.run(arguments)

    def _arguments(
        self, document_name: str = DOCUMENT_NAME, output_directory: Path | None = None
    ) -> CommandLineArguments:
        return CommandLineArguments(
            document_name=document_name,
            input_directory=self._input_directory,
            output_directory=output_directory,
        )

    def _expected_directory(self) -> Path:
        return self._document_path.resolve().parent / "análisis"

    def _build_services(
        self,
        model_name: str,
        uses_local_language_model: bool = True,
        warms_up_language_model: bool = True,
        prompt_source: PromptSourceDTO = DEFAULT_PROMPT_SOURCE,
    ) -> CliAnalysisServices:
        return CliAnalysisServices(
            analyze_document_use_case=self._analyze_document_use_case,
            word_report_use_case=self._word_report_use_case,
            json_report_use_case=self._json_report_use_case,
            html_report_use_case=self._html_report_use_case,
            ensure_language_model_server_use_case=self._ensure_language_model_server_use_case,
            release_language_model_server_use_case=self._release_language_model_server_use_case,
            warm_up_language_model_use_case=self._warm_up_language_model_use_case,
            model_name=model_name,
            uses_local_language_model=uses_local_language_model,
            warms_up_language_model=warms_up_language_model,
            prompt_source=prompt_source,
        )

    def test_releases_server_after_successful_run(self):
        self._run(self._arguments())

        self._release_language_model_server_use_case.execute.assert_called_once()

    def test_releases_server_after_failing_analysis(self):
        self._analyze_document_use_case.execute.side_effect = RuntimeError("Analysis error")

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self._release_language_model_server_use_case.execute.assert_called_once()

    def test_releases_server_after_failing_server_step(self):
        self._ensure_language_model_server_use_case.execute.side_effect = (
            LanguageModelServerStartFailed()
        )

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self._release_language_model_server_use_case.execute.assert_called_once()

    def test_failing_release_turns_successful_run_into_failure_status(self):
        self._release_language_model_server_use_case.execute.side_effect = RuntimeError(
            "Release failed"
        )

        with self.assertLogs(level="ERROR"):
            status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self._release_language_model_server_use_case.execute.assert_called_once()
        self.assertEqual(
            self._printed_lines[-1],
            "❌ No se pudo liberar el servidor del modelo de lenguaje: Release failed",
        )

    def test_failing_release_does_not_hide_original_error(self):
        self._analyze_document_use_case.execute.side_effect = LanguageModelUnavailable()
        self._release_language_model_server_use_case.execute.side_effect = RuntimeError(
            "Release failed"
        )

        with self.assertLogs(level="ERROR"):
            status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self._release_language_model_server_use_case.execute.assert_called_once()
        self.assertEqual(self._printed_lines[-2], f"❌ {LanguageModelUnavailable.MESSAGE}")
        self.assertEqual(
            self._printed_lines[-1],
            "❌ No se pudo liberar el servidor del modelo de lenguaje: Release failed",
        )

    def test_releases_server_after_keyboard_interrupt(self):
        self._analyze_document_use_case.execute.side_effect = KeyboardInterrupt()

        status = self._run(self._arguments())

        self.assertEqual(status, DocumentAnalysisCommand.INTERRUPTED_STATUS)
        self._release_language_model_server_use_case.execute.assert_called_once()

    def test_failing_release_after_keyboard_interrupt_keeps_interrupted_status(self):
        self._analyze_document_use_case.execute.side_effect = KeyboardInterrupt()
        self._release_language_model_server_use_case.execute.side_effect = RuntimeError(
            "Release failed"
        )

        with self.assertLogs(level="ERROR"):
            status = self._run(self._arguments())

        self.assertEqual(status, DocumentAnalysisCommand.INTERRUPTED_STATUS)
        self._release_language_model_server_use_case.execute.assert_called_once()
        self.assertIn(
            "❌ No se pudo liberar el servidor del modelo de lenguaje: Release failed",
            self._printed_lines,
        )
        self.assertEqual(self._printed_lines[-1], "❌ Análisis interrumpido por el usuario")

    def test_release_is_not_called_when_services_factory_fails(self):
        self._services_factory.side_effect = RuntimeError("Services wiring failed")

        status = self._run(self._arguments())

        self.assertEqual(status, 1)
        self._release_language_model_server_use_case.execute.assert_not_called()

    def test_external_model_skips_server_verification_and_warm_up_steps(self):
        services = self._build_services(
            self.MODEL_NAME,
            uses_local_language_model=False,
            warms_up_language_model=False,
        )
        self._services_factory.return_value = services

        status = self._run(self._arguments())

        self.assertEqual(status, 0)
        self._ensure_language_model_server_use_case.execute.assert_not_called()
        self._warm_up_language_model_use_case.execute.assert_not_called()
        self.assertNotIn(
            "Verificando el servidor del modelo de lenguaje", "".join(self._printed_lines)
        )
        self.assertNotIn("Precargando el modelo de lenguaje", "".join(self._printed_lines))
        self._release_language_model_server_use_case.execute.assert_called_once()

    def test_local_model_with_warmup_disabled_runs_only_server_verification(self):
        services = self._build_services(
            self.MODEL_NAME,
            uses_local_language_model=True,
            warms_up_language_model=False,
        )
        self._services_factory.return_value = services

        status = self._run(self._arguments())

        self.assertEqual(status, 0)
        self._ensure_language_model_server_use_case.execute.assert_called_once()
        self._warm_up_language_model_use_case.execute.assert_not_called()
        self.assertIn(
            "Verificando el servidor del modelo de lenguaje", "".join(self._printed_lines)
        )
        self.assertNotIn("Precargando el modelo de lenguaje", "".join(self._printed_lines))
        self._release_language_model_server_use_case.execute.assert_called_once()

    def test_local_model_with_warmup_enabled_runs_both_steps_in_order(self):
        services = self._build_services(
            self.MODEL_NAME,
            uses_local_language_model=True,
            warms_up_language_model=True,
        )
        self._services_factory.return_value = services

        status = self._run(self._arguments())

        self.assertEqual(status, 0)
        self._ensure_language_model_server_use_case.execute.assert_called_once()
        self._warm_up_language_model_use_case.execute.assert_called_once()
        announcements = "".join(self._printed_lines)
        server_step_index = announcements.index("Verificando el servidor del modelo de lenguaje")
        warmup_step_index = announcements.index("Precargando el modelo de lenguaje")
        self.assertLess(server_step_index, warmup_step_index)

    @staticmethod
    def _successful_export_use_case() -> MagicMock:
        export_use_case = MagicMock(spec=ExportReportUseCase)
        export_use_case.execute.return_value = True
        return export_use_case
