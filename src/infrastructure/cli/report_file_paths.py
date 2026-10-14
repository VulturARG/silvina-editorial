from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReportFilePaths:
    """Locations of the Word, JSON and HTML reports generated for one document."""

    word_path: Path
    json_path: Path
    html_path: Path
