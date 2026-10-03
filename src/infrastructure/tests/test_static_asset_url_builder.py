from os import utime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.infrastructure.fastapi.src.utils.static_asset_url_builder import (
    StaticAssetUrlBuilder,
)


class TestStaticAssetUrlBuilder(TestCase):
    """Unit tests for static asset URL builder with cache busting."""

    def test_build_appends_integer_modification_time_for_existing_asset(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            static_directory_path = Path(temporary_directory)
            css_directory = static_directory_path / "css"
            css_directory.mkdir()
            stylesheet_file = css_directory / "silvina.css"
            stylesheet_file.write_text("body { color: black; }", encoding="utf-8")
            expected_timestamp = int(stylesheet_file.stat().st_mtime)

            builder = StaticAssetUrlBuilder(static_directory_path)
            result = builder.build("/static/css/silvina.css")

            self.assertEqual(result, f"/static/css/silvina.css?v={expected_timestamp}")

    def test_build_reflects_changed_modification_time_after_touch(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            static_directory_path = Path(temporary_directory)
            stylesheet_file = static_directory_path / "silvina.css"
            stylesheet_file.write_text("body { color: black; }", encoding="utf-8")
            initial_timestamp = 1_700_000_000
            utime(stylesheet_file, (initial_timestamp, initial_timestamp))

            builder = StaticAssetUrlBuilder(static_directory_path)
            self.assertEqual(
                builder.build("/static/silvina.css"),
                f"/static/silvina.css?v={initial_timestamp}",
            )

            updated_timestamp = 1_800_000_000
            utime(stylesheet_file, (updated_timestamp, updated_timestamp))
            self.assertEqual(
                builder.build("/static/silvina.css"),
                f"/static/silvina.css?v={updated_timestamp}",
            )

    def test_build_returns_unknown_file_path_unchanged(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            static_directory_path = Path(temporary_directory)
            builder = StaticAssetUrlBuilder(static_directory_path)

            result = builder.build("/static/css/unknown.css")

            self.assertEqual(result, "/static/css/unknown.css")

    def test_build_returns_traversal_path_unchanged(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            static_directory_path = Path(temporary_directory)
            builder = StaticAssetUrlBuilder(static_directory_path)

            self.assertEqual(
                builder.build("/static/../outside.css"),
                "/static/../outside.css",
            )
            self.assertEqual(
                builder.build("/static/subdir/../../outside.css"),
                "/static/subdir/../../outside.css",
            )
            self.assertEqual(builder.build("../outside.css"), "../outside.css")
