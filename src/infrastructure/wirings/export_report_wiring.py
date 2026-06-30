from os.path import join

from src.application.export_report_use_case import ExportReportUseCase
from src.infrastructure.adapters.report.docx_report_adapter import DocxReportAdapter
from src.infrastructure.adapters.report.docx_report_settings import DocxReportSettings
from src.infrastructure.resources.assets import ASSETS_DIR


class ExportReportWiring:
    """Factory for building a ready-to-use ExportReportUseCase."""

    def create_use_case(self) -> ExportReportUseCase:
        adapter = DocxReportAdapter(
            logo_path=join(ASSETS_DIR, "logo.jpg"),
            settings=DocxReportSettings(),
        )
        return ExportReportUseCase(report_export_port=adapter)
