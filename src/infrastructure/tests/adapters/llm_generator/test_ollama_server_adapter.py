from subprocess import DEVNULL
from unittest import TestCase
from unittest.mock import MagicMock, patch

from httpx import ConnectTimeout
from httpx import RequestError as HttpxRequestError
from ollama import RequestError as OllamaRequestError
from ollama import ResponseError as OllamaResponseError

from src.domain.exceptions.language_model_errors import (
    LanguageModelServerExecutableNotFound,
    LanguageModelServerStartFailed,
)
from src.domain.language_model.language_model_server_port import LanguageModelServerPort
from src.infrastructure.adapters.llm_generator.ollama_server_adapter import (
    OllamaServerAdapter,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease import (
    OllamaServerLease,
)
from src.infrastructure.adapters.llm_generator.ollama_server_lease_store import (
    OllamaServerLeaseStore,
)
from src.infrastructure.adapters.llm_generator.process_inspector import (
    ProcessInspector,
)
from src.infrastructure.adapters.llm_generator.windows_creation_flags import (
    CREATE_NEW_PROCESS_GROUP,
    CREATE_NO_WINDOW,
)


class TestOllamaServerAdapter(TestCase):
    BASE_URL = "http://127.0.0.1:11434"

    def test_is_subclass_of_language_model_server_port(self):
        self.assertTrue(issubclass(OllamaServerAdapter, LanguageModelServerPort))

    def test_is_running_returns_true_when_client_list_succeeds(self):
        fake_client = MagicMock()
        fake_client.list.return_value = {"models": []}
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            client_factory=lambda host, timeout: fake_client,
        )

        self.assertTrue(adapter.is_running())

    def test_is_running_returns_false_when_connection_error_is_raised(self):
        fake_client = MagicMock()
        fake_client.list.side_effect = ConnectionError("Connection refused")
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            client_factory=lambda host, timeout: fake_client,
        )

        self.assertFalse(adapter.is_running())

    def test_is_running_returns_false_when_httpx_request_error_is_raised(self):
        fake_client = MagicMock()
        fake_client.list.side_effect = HttpxRequestError("Network error")
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            client_factory=lambda host, timeout: fake_client,
        )

        self.assertFalse(adapter.is_running())

    def test_is_running_returns_false_when_httpx_connect_timeout_is_raised(self):
        fake_client = MagicMock()
        fake_client.list.side_effect = ConnectTimeout("Connection timed out")
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            client_factory=lambda host, timeout: fake_client,
        )

        self.assertFalse(adapter.is_running())

    def test_is_running_returns_false_when_ollama_request_error_is_raised(self):
        fake_client = MagicMock()
        fake_client.list.side_effect = OllamaRequestError("Ollama request failed")
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            client_factory=lambda host, timeout: fake_client,
        )

        self.assertFalse(adapter.is_running())

    def test_is_running_returns_false_when_ollama_response_error_is_raised(self):
        fake_client = MagicMock()
        fake_client.list.side_effect = OllamaResponseError("Server error", 500)
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            client_factory=lambda host, timeout: fake_client,
        )

        self.assertFalse(adapter.is_running())

    def test_start_raises_language_model_server_start_failed_when_host_is_not_local(self):
        process_launcher = MagicMock()
        adapter = OllamaServerAdapter(
            base_url="http://remote-server.lan:11434",
            process_launcher=process_launcher,
        )

        with self.assertRaises(LanguageModelServerStartFailed):
            adapter.start()

        process_launcher.assert_not_called()

    def test_start_raises_language_model_server_start_failed_when_ip_is_not_local(self):
        process_launcher = MagicMock()
        adapter = OllamaServerAdapter(
            base_url="http://192.168.1.100:11434",
            process_launcher=process_launcher,
        )

        with self.assertRaises(LanguageModelServerStartFailed):
            adapter.start()

        process_launcher.assert_not_called()

    def test_start_raises_language_model_server_start_failed_when_executable_not_found(self):
        process_launcher = MagicMock()
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: None,
            process_launcher=process_launcher,
        )

        with self.assertRaises(LanguageModelServerStartFailed):
            adapter.start()

        process_launcher.assert_not_called()

    def test_start_raises_language_model_server_executable_not_found_when_executable_not_found(
        self,
    ):
        process_launcher = MagicMock()
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda: None,
            process_launcher=process_launcher,
        )

        with self.assertRaises(LanguageModelServerExecutableNotFound):
            adapter.start()

        process_launcher.assert_not_called()

    def test_start_raises_language_model_server_start_failed_when_launcher_raises_os_error(self):
        def failing_launcher(*args, **kwargs):
            raise OSError("Access denied")

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "/usr/bin/ollama",
            process_launcher=failing_launcher,
        )

        with self.assertRaises(LanguageModelServerStartFailed):
            adapter.start()

    def test_start_launches_serve_with_detached_flags_on_windows(self):
        process_launcher = MagicMock()
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "C:\\bin\\ollama.exe",
            process_launcher=process_launcher,
            startup_timeout_seconds=5.0,
            poll_interval_seconds=0.1,
            sleep_function=MagicMock(),
            clock_function=MagicMock(side_effect=[0.0, 0.1, 0.2]),
            client_factory=lambda host, timeout: MagicMock(),
        )

        with patch("src.infrastructure.adapters.llm_generator.ollama_server_adapter.name", "nt"):
            adapter.start()

        expected_flags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        process_launcher.assert_called_once_with(
            ["C:\\bin\\ollama.exe", "serve"],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            creationflags=expected_flags,
        )

    def test_start_launches_serve_with_start_new_session_on_posix(self):
        process_launcher = MagicMock()
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "/usr/local/bin/ollama",
            process_launcher=process_launcher,
            startup_timeout_seconds=5.0,
            poll_interval_seconds=0.1,
            sleep_function=MagicMock(),
            clock_function=MagicMock(side_effect=[0.0, 0.1, 0.2]),
            client_factory=lambda host, timeout: MagicMock(),
        )

        with patch("src.infrastructure.adapters.llm_generator.ollama_server_adapter.name", "posix"):
            adapter.start()

        process_launcher.assert_called_once_with(
            ["/usr/local/bin/ollama", "serve"],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            start_new_session=True,
        )

    def test_start_polls_until_server_responds(self):
        call_times = [0.0, 0.5, 1.0, 1.5]
        fake_client = MagicMock()
        fake_client.list.side_effect = [
            ConnectionError("Server starting"),
            {"models": []},
        ]
        sleep_mock = MagicMock()

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "/bin/ollama",
            process_launcher=MagicMock(),
            startup_timeout_seconds=5.0,
            poll_interval_seconds=0.5,
            sleep_function=sleep_mock,
            clock_function=lambda: call_times.pop(0) if call_times else 2.0,
            client_factory=lambda host, timeout: fake_client,
        )

        adapter.start()

        self.assertEqual(fake_client.list.call_count, 2)
        sleep_mock.assert_called_with(0.5)

    def test_start_raises_language_model_server_start_failed_when_startup_times_out(self):
        call_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
        fake_client = MagicMock()
        fake_client.list.side_effect = ConnectionError("Never starts")

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "/bin/ollama",
            process_launcher=MagicMock(),
            startup_timeout_seconds=1.0,
            poll_interval_seconds=0.5,
            sleep_function=MagicMock(),
            clock_function=lambda: call_times.pop(0) if call_times else 10.0,
            client_factory=lambda host, timeout: fake_client,
        )

        with self.assertRaises(LanguageModelServerStartFailed):
            adapter.start()

    def test_start_writes_lease_and_launches_watcher_on_windows(self):
        process_launcher = MagicMock()
        mock_process = MagicMock()
        mock_process.pid = 4321
        process_launcher.return_value = mock_process
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_clock = MagicMock(return_value=123456.0)

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "C:\\bin\\ollama.exe",
            process_launcher=process_launcher,
            startup_timeout_seconds=5.0,
            poll_interval_seconds=0.1,
            sleep_function=MagicMock(),
            clock_function=MagicMock(side_effect=[0.0, 0.1, 0.2]),
            client_factory=lambda host, timeout: MagicMock(),
            lease_store=fake_lease_store,
            current_process_id_provider=lambda: 9876,
            wall_clock_function=fake_clock,
            watcher_launch_command=["python", "-m", "watcher"],
            watcher_working_directory="C:\\project",
        )

        with patch("src.infrastructure.adapters.llm_generator.ollama_server_adapter.name", "nt"):
            adapter.start()

        self.assertEqual(process_launcher.call_count, 2)
        fake_lease_store.write.assert_called_once()
        written_lease = fake_lease_store.write.call_args.args[0]
        self.assertEqual(written_lease.server_process_id, 4321)
        self.assertEqual(written_lease.active_process_id, 9876)
        self.assertEqual(written_lease.last_use_epoch_seconds, 123456.0)

        expected_flags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        process_launcher.assert_called_with(
            ["python", "-m", "watcher", "--server-process-id", "4321"],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            creationflags=expected_flags,
            cwd="C:\\project",
        )

    def test_start_continues_when_lease_store_write_raises_os_error(self):
        process_launcher = MagicMock()
        mock_process = MagicMock()
        mock_process.pid = 4321
        process_launcher.return_value = mock_process
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.write.side_effect = OSError("read-only filesystem")

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "/bin/ollama",
            process_launcher=process_launcher,
            startup_timeout_seconds=5.0,
            poll_interval_seconds=0.1,
            sleep_function=MagicMock(),
            clock_function=MagicMock(side_effect=[0.0, 0.1, 0.2]),
            client_factory=lambda host, timeout: MagicMock(),
            lease_store=fake_lease_store,
        )

        with patch("src.infrastructure.adapters.llm_generator.ollama_server_adapter.name", "posix"):
            adapter.start()

    def test_start_continues_when_watcher_launch_raises_os_error(self):
        process_launcher = MagicMock()
        mock_process = MagicMock()
        mock_process.pid = 4321
        process_launcher.side_effect = [mock_process, OSError("spawn failed")]
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            executable_locator=lambda command_name: "/bin/ollama",
            process_launcher=process_launcher,
            startup_timeout_seconds=5.0,
            poll_interval_seconds=0.1,
            sleep_function=MagicMock(),
            clock_function=MagicMock(side_effect=[0.0, 0.1, 0.2]),
            client_factory=lambda host, timeout: MagicMock(),
            lease_store=fake_lease_store,
            watcher_launch_command=["python", "-m", "watcher"],
        )

        with patch("src.infrastructure.adapters.llm_generator.ollama_server_adapter.name", "posix"):
            adapter.start()

    def test_mark_in_use_does_nothing_when_lease_is_none(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = None
        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
        )

        adapter.mark_in_use()

        fake_lease_store.write.assert_not_called()
        fake_lease_store.clear.assert_not_called()

    def test_mark_in_use_clears_lease_when_server_process_is_not_alive(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = OllamaServerLease(
            server_process_id=4321,
            active_process_id=None,
            last_use_epoch_seconds=100.0,
        )
        fake_inspector = MagicMock(spec=ProcessInspector)
        fake_inspector.image_name.return_value = None

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
            process_inspector=fake_inspector,
        )

        adapter.mark_in_use()

        fake_lease_store.clear.assert_called_once()
        fake_lease_store.write.assert_not_called()

    def test_mark_in_use_clears_lease_when_server_image_is_not_ollama(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = OllamaServerLease(
            server_process_id=4321,
            active_process_id=None,
            last_use_epoch_seconds=100.0,
        )
        fake_inspector = MagicMock(spec=ProcessInspector)
        fake_inspector.image_name.return_value = "notepad.exe"

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
            process_inspector=fake_inspector,
        )

        adapter.mark_in_use()

        fake_lease_store.clear.assert_called_once()
        fake_lease_store.write.assert_not_called()

    def test_mark_in_use_updates_lease_with_active_process_id_and_current_time(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = OllamaServerLease(
            server_process_id=4321,
            active_process_id=None,
            last_use_epoch_seconds=100.0,
        )
        fake_inspector = MagicMock(spec=ProcessInspector)
        fake_inspector.image_name.return_value = "ollama.exe"

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
            process_inspector=fake_inspector,
            current_process_id_provider=lambda: 9876,
            wall_clock_function=lambda: 200.0,
        )

        adapter.mark_in_use()

        fake_lease_store.write.assert_called_once()
        written = fake_lease_store.write.call_args.args[0]
        self.assertEqual(written.server_process_id, 4321)
        self.assertEqual(written.active_process_id, 9876)
        self.assertEqual(written.last_use_epoch_seconds, 200.0)

    def test_mark_in_use_does_not_raise_when_lease_write_fails(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = OllamaServerLease(
            server_process_id=4321,
            active_process_id=None,
            last_use_epoch_seconds=100.0,
        )
        fake_lease_store.write.side_effect = OSError("disk full")
        fake_inspector = MagicMock(spec=ProcessInspector)
        fake_inspector.image_name.return_value = "ollama.exe"

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
            process_inspector=fake_inspector,
        )

        adapter.mark_in_use()

    def test_mark_idle_does_nothing_when_lease_is_none(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = None

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
        )

        adapter.mark_idle()

        fake_lease_store.write.assert_not_called()

    def test_mark_idle_updates_lease_with_none_active_process_id_and_current_time(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = OllamaServerLease(
            server_process_id=4321,
            active_process_id=9876,
            last_use_epoch_seconds=100.0,
        )

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
            wall_clock_function=lambda: 250.0,
        )

        adapter.mark_idle()

        fake_lease_store.write.assert_called_once()
        written = fake_lease_store.write.call_args.args[0]
        self.assertEqual(written.server_process_id, 4321)
        self.assertIsNone(written.active_process_id)
        self.assertEqual(written.last_use_epoch_seconds, 250.0)

    def test_mark_idle_does_not_raise_when_lease_write_fails(self):
        fake_lease_store = MagicMock(spec=OllamaServerLeaseStore)
        fake_lease_store.read.return_value = OllamaServerLease(
            server_process_id=4321,
            active_process_id=9876,
            last_use_epoch_seconds=100.0,
        )
        fake_lease_store.write.side_effect = OSError("disk full")

        adapter = OllamaServerAdapter(
            base_url=self.BASE_URL,
            lease_store=fake_lease_store,
        )

        adapter.mark_idle()
