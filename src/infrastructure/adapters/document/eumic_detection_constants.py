"""Technical constants for EUMIC document format detection."""

FIGURE_NUMBERING_PATTERN: str = r"figura\s+(\d+)"
TABLE_NUMBERING_PATTERN: str = r"tabla\s+(\d+)"
ABSTRACT_PARAGRAPH_LOOKAHEAD: int = 5
