from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.infrastructure.adapters.llm_generator.ollama_server_lease import (
    OllamaServerLease,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease_store import (
    OllamaServerLeaseStore,
)


class TestOllamaServerLeaseStore(TestCase):
    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self._temporary_path = Path(self._temporary_directory.name)
        self._lease_file_path = self._temporary_path / "data" / "ollama_server_lease.json"
        self._store = OllamaServerLeaseStore(self._lease_file_path)

    def test_read_returns_none_when_file_does_not_exist(self):
        lease = self._store.read()

        self.assertIsNone(lease)

    def test_read_returns_none_when_file_is_empty(self):
        self._lease_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lease_file_path.write_text("", encoding="utf-8")

        lease = self._store.read()

        self.assertIsNone(lease)

    def test_read_returns_none_when_file_contains_invalid_json(self):
        self._lease_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lease_file_path.write_text("{not valid json", encoding="utf-8")

        lease = self._store.read()

        self.assertIsNone(lease)

    def test_read_returns_none_when_json_is_missing_required_fields(self):
        self._lease_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lease_file_path.write_text('{"server_process_id": 1234}', encoding="utf-8")

        lease = self._store.read()

        self.assertIsNone(lease)

    def test_write_and_read_round_trip(self):
        lease = OllamaServerLease(
            server_process_id=1234,
            active_process_id=5678,
            last_use_epoch_seconds=1700000000.5,
        )

        self._store.write(lease)
        loaded_lease = self._store.read()

        self.assertEqual(loaded_lease, lease)

    def test_write_and_read_round_trip_with_none_active_process_id(self):
        lease = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1700000000.5,
        )

        self._store.write(lease)
        loaded_lease = self._store.read()

        self.assertEqual(loaded_lease, lease)

    def test_write_atomically_leaves_no_temporary_sibling_files(self):
        lease = OllamaServerLease(
            server_process_id=1234,
            active_process_id=5678,
            last_use_epoch_seconds=1700000000.5,
        )

        self._store.write(lease)

        parent_directory_files = list(self._lease_file_path.parent.iterdir())
        self.assertEqual(parent_directory_files, [self._lease_file_path])

    def test_write_raises_os_error_on_filesystem_failure(self):
        lease = OllamaServerLease(
            server_process_id=1234,
            active_process_id=5678,
            last_use_epoch_seconds=1700000000.5,
        )

        with patch("pathlib.Path.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self._store.write(lease)

    def test_clear_removes_existing_file(self):
        lease = OllamaServerLease(
            server_process_id=1234,
            active_process_id=5678,
            last_use_epoch_seconds=1700000000.5,
        )
        self._store.write(lease)
        self.assertTrue(self._lease_file_path.exists())

        self._store.clear()

        self.assertFalse(self._lease_file_path.exists())

    def test_clear_when_file_does_not_exist_does_not_raise(self):
        self._store.clear()
