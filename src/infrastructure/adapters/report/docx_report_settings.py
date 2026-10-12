from dataclasses import dataclass

from src.domain.enums.allowed_font import AllowedFont


@dataclass(frozen=True)
class DocxReportSettings:
    """Runtime configuration for the Word (.docx) report adapter.

    `app_name` through `max_replacements` are deployment config with no
    defaults — the wiring layer MUST inject them from `EnvConfig`. The
    remaining fields are Word template visual constants — not deployment
    config — and keep static defaults.
    """

    app_name: str
    app_version: str
    score_high_threshold: float
    score_medium_threshold: float
    publish_threshold: float
    words_per_page: int
    max_errors_displayed: int
    context_truncation_limit: int
    max_replacements: int

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
    feedback_item_indent_inches: tuple[float, float, float] = (0.25, 0.5, 0.75)
