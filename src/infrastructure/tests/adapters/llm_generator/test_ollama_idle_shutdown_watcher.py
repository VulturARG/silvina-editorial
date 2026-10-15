from unittest import TestCase
from unittest.mock import MagicMock

from src.infrastructure.adapters.llm_generator.ollama_idle_shutdown_watcher import (
    OllamaIdleShutdownWatcher,
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
from src.infrastructure.adapters.llm_generator.process_tree_terminator import (
    ProcessTreeTerminator,
)


class FakeClock:
    def __init__(self, current_time: float = 1000.0) -> None:
        self.current_time = current_time

    def time(self) -> float:
        return self.current_time

    def sleep(self, seconds: float) -> None:
        self.current_time += seconds


class TestOllamaIdleShutdownWatcher(TestCase):
    def setUp(self) -> None:
        self._fake_clock = FakeClock(current_time=1000.0)
        self._lease_store = MagicMock(spec=OllamaServerLeaseStore)
        self._process_inspector = MagicMock(spec=ProcessInspector)
        self._process_inspector.is_alive.side_effect = lambda process_id: process_id == 1234
        self._process_inspector.image_name.return_value = "ollama.exe"
        self._process_tree_terminator = MagicMock(spec=ProcessTreeTerminator)

    def _create_watcher(
        self,
        server_process_id: int = 1234,
        idle_seconds: float = 300.0,
        poll_interval_seconds: float = 10.0,
    ) -> OllamaIdleShutdownWatcher:
        return OllamaIdleShutdownWatcher(
            server_process_id=server_process_id,
            lease_store=self._lease_store,
            process_inspector=self._process_inspector,
            process_tree_terminator=self._process_tree_terminator,
            idle_seconds=idle_seconds,
            poll_interval_seconds=poll_interval_seconds,
            sleep_function=self._fake_clock.sleep,
            wall_clock_function=self._fake_clock.time,
        )

    def test_exits_when_lease_is_none(self):
        self._lease_store.read.return_value = None
        watcher = self._create_watcher()

        watcher.run()

        self._process_tree_terminator.terminate.assert_not_called()
        self._lease_store.clear.assert_not_called()

    def test_exits_when_lease_server_process_id_differs(self):
        self._lease_store.read.return_value = OllamaServerLease(
            server_process_id=9999,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        watcher = self._create_watcher(server_process_id=1234)

        watcher.run()

        self._process_tree_terminator.terminate.assert_not_called()
        self._lease_store.clear.assert_not_called()

    def test_server_process_dead_clears_lease_and_returns_without_terminating(self):
        self._lease_store.read.return_value = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        self._process_inspector.is_alive.side_effect = None
        self._process_inspector.is_alive.return_value = False
        watcher = self._create_watcher(server_process_id=1234)

        watcher.run()

        self._process_tree_terminator.terminate.assert_not_called()
        self._lease_store.clear.assert_called_once()

    def test_server_process_alive_keeps_watcher_polling(self):
        lease = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        poll_count = 0

        def _read_lease_three_times():
            nonlocal poll_count
            poll_count += 1
            if poll_count <= 3:
                return lease
            return None

        self._lease_store.read.side_effect = _read_lease_three_times
        watcher = self._create_watcher(
            server_process_id=1234,
            idle_seconds=300.0,
            poll_interval_seconds=10.0,
        )

        watcher.run()

        self.assertEqual(poll_count, 4)
        self.assertEqual(self._fake_clock.current_time, 1040.0)
        self._process_tree_terminator.terminate.assert_not_called()
        self._lease_store.clear.assert_not_called()

    def test_startup_scenario_alive_process_terminates_after_idle_expiry(self):
        self._lease_store.read.return_value = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        watcher = self._create_watcher(
            server_process_id=1234,
            idle_seconds=300.0,
            poll_interval_seconds=50.0,
        )

        watcher.run()

        self.assertEqual(self._fake_clock.current_time, 1300.0)
        self._process_tree_terminator.terminate.assert_called_once_with(1234)
        self._lease_store.clear.assert_called_once()

    def test_continues_loop_and_does_not_terminate_while_active_process_is_alive(self):
        lease_with_active = OllamaServerLease(
            server_process_id=1234,
            active_process_id=5555,
            last_use_epoch_seconds=500.0,
        )
        lease_after_release = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1200.0,
        )

        def _dynamic_lease():
            if self._fake_clock.current_time < 1200.0:
                return lease_with_active
            return lease_after_release

        def _dynamic_is_alive(process_id: int) -> bool:
            if process_id == 1234:
                return True
            return self._fake_clock.current_time < 1200.0

        self._lease_store.read.side_effect = _dynamic_lease
        self._process_inspector.is_alive.side_effect = _dynamic_is_alive
        watcher = self._create_watcher(
            server_process_id=1234,
            idle_seconds=300.0,
            poll_interval_seconds=50.0,
        )

        watcher.run()

        self.assertGreaterEqual(self._fake_clock.current_time, 1500.0)
        self._process_tree_terminator.terminate.assert_called_once_with(1234)
        self._lease_store.clear.assert_called_once()

    def test_terminates_server_and_clears_lease_when_idle_duration_exceeded(self):
        self._lease_store.read.return_value = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        watcher = self._create_watcher(server_process_id=1234, idle_seconds=300.0)

        watcher.run()

        self._process_tree_terminator.terminate.assert_called_once_with(1234)
        self._lease_store.clear.assert_called_once()

    def test_does_not_terminate_when_image_name_does_not_start_with_ollama(self):
        self._lease_store.read.return_value = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        self._process_inspector.image_name.return_value = "notepad.exe"
        watcher = self._create_watcher(server_process_id=1234, idle_seconds=300.0)

        watcher.run()

        self._process_tree_terminator.terminate.assert_not_called()
        self._lease_store.clear.assert_called_once()

    def test_reuse_within_idle_window_resets_idle_countdown(self):
        lease_initial = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1000.0,
        )
        lease_renewed = OllamaServerLease(
            server_process_id=1234,
            active_process_id=None,
            last_use_epoch_seconds=1200.0,
        )

        def _dynamic_lease():
            if self._fake_clock.current_time < 1200.0:
                return lease_initial
            return lease_renewed

        self._lease_store.read.side_effect = _dynamic_lease
        watcher = self._create_watcher(
            server_process_id=1234,
            idle_seconds=300.0,
            poll_interval_seconds=50.0,
        )

        watcher.run()

        self.assertEqual(self._fake_clock.current_time, 1500.0)
        self._process_tree_terminator.terminate.assert_called_once_with(1234)
        self._lease_store.clear.assert_called_once()
