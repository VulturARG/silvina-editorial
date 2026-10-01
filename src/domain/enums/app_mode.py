from enum import Enum


class AppMode(Enum):
    """Application operational mode for privacy and telemetry."""

    DEBUG = "DEBUG"
    PROD = "PROD"
