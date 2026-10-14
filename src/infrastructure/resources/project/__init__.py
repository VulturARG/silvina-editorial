from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).resolve().parents[4]
SETTINGS_FILE_PATH = PROJECT_ROOT_DIR / "analysis_settings.toml"
VERSION_FILE_PATH = PROJECT_ROOT_DIR / "version.txt"
EDITORIAL_NORMS_FILE_PATH = PROJECT_ROOT_DIR / "editorial_norms.toml"
