from pathlib import Path
from unittest import TestCase

from src.infrastructure.resources.project import (
    EDITORIAL_NORMS_FILE_PATH,
    PROJECT_ROOT_DIR,
    SETTINGS_FILE_PATH,
    VERSION_FILE_PATH,
)


class TestProjectResources(TestCase):
    def test_exposes_project_root_dir_as_path(self):
        self.assertIsInstance(PROJECT_ROOT_DIR, Path)

    def test_exposes_settings_file_path_as_path(self):
        self.assertIsInstance(SETTINGS_FILE_PATH, Path)

    def test_exposes_version_file_path_as_path(self):
        self.assertIsInstance(VERSION_FILE_PATH, Path)

    def test_exposes_editorial_norms_file_path_as_path(self):
        self.assertIsInstance(EDITORIAL_NORMS_FILE_PATH, Path)

    def test_project_root_dir_contains_main_py(self):
        self.assertTrue((PROJECT_ROOT_DIR / "main.py").is_file())

    def test_settings_file_path_points_to_existing_file_in_project_root(self):
        self.assertEqual(SETTINGS_FILE_PATH.name, "analysis_settings.toml")
        self.assertEqual(SETTINGS_FILE_PATH.parent, PROJECT_ROOT_DIR)
        self.assertTrue(SETTINGS_FILE_PATH.is_file())

    def test_version_file_path_points_to_existing_file_in_project_root(self):
        self.assertEqual(VERSION_FILE_PATH.name, "version.txt")
        self.assertEqual(VERSION_FILE_PATH.parent, PROJECT_ROOT_DIR)
        self.assertTrue(VERSION_FILE_PATH.is_file())

    def test_editorial_norms_file_path_points_to_existing_file_in_project_root(self):
        self.assertEqual(EDITORIAL_NORMS_FILE_PATH.name, "editorial_norms.toml")
        self.assertEqual(EDITORIAL_NORMS_FILE_PATH.parent, PROJECT_ROOT_DIR)
        self.assertTrue(EDITORIAL_NORMS_FILE_PATH.is_file())
