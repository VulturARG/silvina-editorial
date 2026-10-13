from pathlib import Path
from unittest import TestCase

from src.infrastructure.cli.console_step_announcer import ConsoleStepAnnouncer


class TestConsoleStepAnnouncer(TestCase):
    def setUp(self):
        self.written_lines: list[str] = []
        self.announcer = ConsoleStepAnnouncer(write_function=self.written_lines.append)

    def test_announce_start_writes_pending_line(self):
        self.announcer.announce_start("Analizando documento")

        self.assertEqual(self.written_lines, ["⏳ Analizando documento..."])

    def test_announce_finish_writes_done_line(self):
        self.announcer.announce_finish("Analizando documento")

        self.assertEqual(self.written_lines, ["✅ Analizando documento: terminado"])

    def test_announce_error_writes_error_line(self):
        self.announcer.announce_error("El documento no existe")

        self.assertEqual(self.written_lines, ["❌ El documento no existe"])

    def test_announce_completion_writes_header_and_one_line_per_path(self):
        self.announcer.announce_completion([Path("tesis.docx"), Path("tesis.json")])

        self.assertEqual(
            self.written_lines,
            ["🎉 Ejecución terminada", "   📄 tesis.docx", "   📄 tesis.json"],
        )

    def test_announce_completion_without_paths_writes_only_header(self):
        self.announcer.announce_completion([])

        self.assertEqual(self.written_lines, ["🎉 Ejecución terminada"])

    def test_step_writes_start_then_finish_when_body_succeeds(self):
        with self.announcer.step("Generando informe"):
            self.written_lines.append("cuerpo")

        self.assertEqual(
            self.written_lines,
            ["⏳ Generando informe...", "cuerpo", "✅ Generando informe: terminado"],
        )

    def test_step_writes_only_start_when_body_raises_and_propagates_exception(self):
        with self.assertRaises(ValueError):
            with self.announcer.step("Generando informe"):
                raise ValueError("fallo")

        self.assertEqual(self.written_lines, ["⏳ Generando informe..."])

    def test_nested_steps_announce_finish_in_reverse_order(self):
        with self.announcer.step("Proceso"):
            with self.announcer.step("Subproceso"):
                pass

        self.assertEqual(
            self.written_lines,
            [
                "⏳ Proceso...",
                "⏳ Subproceso...",
                "✅ Subproceso: terminado",
                "✅ Proceso: terminado",
            ],
        )

    def test_failing_outer_step_does_not_announce_its_finish(self):
        with self.assertRaises(ValueError):
            with self.announcer.step("Proceso"):
                with self.announcer.step("Subproceso"):
                    pass
                raise ValueError("fallo")

        self.assertEqual(
            self.written_lines,
            ["⏳ Proceso...", "⏳ Subproceso...", "✅ Subproceso: terminado"],
        )
