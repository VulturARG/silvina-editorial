from pathlib import Path


class StaticAssetUrlBuilder:
    """Build static asset URLs with cache-busting modification time queries."""

    def __init__(self, static_directory_path: Path | str) -> None:
        """Initialize the builder with the root static directory path."""
        self._static_directory_path = Path(static_directory_path).resolve()

    def build(self, path: str) -> str:
        """Return the asset path with an appended modification time query parameter."""
        try:
            clean_path = path.split("?")[0].split("#")[0]
            if clean_path.startswith("/static/"):
                relative_path = clean_path[len("/static/") :]
            elif clean_path.startswith("static/"):
                relative_path = clean_path[len("static/") :]
            else:
                relative_path = clean_path.lstrip("/")

            target_file_path = (self._static_directory_path / relative_path).resolve()
            if not target_file_path.is_relative_to(self._static_directory_path):
                return path

            if not target_file_path.is_file():
                return path

            modification_timestamp = int(target_file_path.stat().st_mtime)
            separator = "&" if "?" in path else "?"
            return f"{path}{separator}v={modification_timestamp}"
        except (OSError, ValueError):
            return path

    def __call__(self, path: str) -> str:
        """Allow the builder instance to be called directly."""
        return self.build(path)
