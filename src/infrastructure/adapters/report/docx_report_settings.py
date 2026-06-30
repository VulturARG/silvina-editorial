from os import environ
from dataclasses import dataclass, field

from src.domain.enums.allowed_font import AllowedFont


@dataclass(frozen=True)
class DocxReportSettings:
    """Runtime configuration for the Word (.docx) report adapter.

    Deployment config fields read from environment (via load_dotenv in wiring).
    Visual design fields are Word template constants — not deployment config.
    """

    app_name: str = field(
        default_factory=lambda: environ.get("SILVINA_APP_NAME", "Silvina Editorial Assistant")
    )
    app_version: str = field(default_factory=lambda: environ.get("SILVINA_VERSION", "0.9"))
    score_high_threshold: float = field(
        default_factory=lambda: float(environ.get("SILVINA_SCORE_HIGH_THRESHOLD", "8.0"))
    )
    score_medium_threshold: float = field(
        default_factory=lambda: float(environ.get("SILVINA_SCORE_MEDIUM_THRESHOLD", "6.0"))
    )

    font_name: str = AllowedFont.CALIBRI.value

    base_font_size_pt: int = 12
    line_spacing: float = 1.15
    heading_color_rgb: tuple[int, int, int] = (0, 51, 102)
    publishable_color_rgb: tuple[int, int, int] = (0, 128, 0)
    reject_color_rgb: tuple[int, int, int] = (192, 0, 0)
    neutral_color_rgb: tuple[int, int, int] = (128, 128, 128)
    warning_color_rgb: tuple[int, int, int] = (255, 140, 0)
    title_font_size_pt: int = 22
    decision_font_size_pt: int = 16
    score_font_size_pt: int = 14
    recommendation_font_size_pt: int = 12
    page_number_font_size_pt: int = 10
    metadata_font_size_pt: int = 9
    table_style: str = "Light Grid Accent 1"
    logo_width_inches: float = 1.8
    header_table_width_inches: float = 6.5
    header_left_cell_width_inches: float = 4.5
    header_right_cell_width_inches: float = 2.0
