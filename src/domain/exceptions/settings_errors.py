from src.domain.exceptions.base_src_error import BaseSrcError


class SettingsError(BaseSrcError):
    """Base class for all settings-related exceptions."""

    def __init__(self, detail: str) -> None:
        """Store the detail that pinpoints the offending file, section, key or variable."""
        super().__init__()
        self.detail = detail

    def dict(self) -> "dict[str, str]":
        """Return the error message followed by its detail."""
        return {"error": f"{super().dict()['error']} {self.detail}"}

    def __str__(self) -> str:
        """Return the same text as the error message dictionary."""
        return self.dict()["error"]


class SettingsFileNotFound(SettingsError):
    """Raised when the settings file cannot be located."""

    MESSAGE = "The settings file could not be found."


class SettingsFileInvalid(SettingsError):
    """Raised when the settings file is not valid TOML."""

    MESSAGE = "The settings file is not valid TOML."


class SettingValueMissing(SettingsError):
    """Raised when a required setting is absent from the settings file and the environment."""

    MESSAGE = "A required setting is missing."


class SettingValueInvalid(SettingsError):
    """Raised when a setting has a value or type that cannot be used."""

    MESSAGE = "A setting has an invalid value."
