from os.path import join

from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.env_config import EnvConfig
from src.infrastructure.resources.assets import ASSETS_DIR


class ExportReportWiring:
    """Factory for building a ready-to-use ExportReportUseCase."""

    def create_use_case(self) -> ExportReportUseCase:
        env_config = EnvConfig()
        settings = DocxReportSettings(
            app_name=env_config.silvina_app_name,
            app_version=env_config.silvina_version,
            score_high_threshold=env_config.report_score_high_threshold,
            score_medium_threshold=env_config.report_score_medium_threshold,
            words_per_page=env_config.report_words_per_page,
            max_errors_displayed=env_config.report_max_errors_displayed,
            context_truncation_limit=env_config.report_context_truncation_limit,
            max_replacements=env_config.report_max_replacements,
        )
        adapter = DocxReportAdapter(
            logo_path=join(ASSETS_DIR, "logo.jpg"),
            docx_report_settings=settings,
        )
        return ExportReportUseCase(report_export_port=adapter)
