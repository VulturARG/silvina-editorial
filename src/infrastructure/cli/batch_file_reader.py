from pathlib import Path
from tomllib import load
from typing import Any

from src.infrastructure.cli.batch_document_selector import BatchDocumentSelector
from src.infrastructure.cli.batch_plan import BatchPlan
from src.infrastructure.cli.batch_run import BatchRun
from src.infrastructure.cli.command_line_arguments import CommandLineArguments


class BatchFileReader:
    """Reads a batch TOML file into a plan with the arguments of every document of every run."""

    BATCH_TABLE_KEY = "batch"
    RUN_TABLE_ARRAY_KEY = "run"
    NAME_KEY = "name"
    DOCUMENTS_KEY = "documents"
    DOCUMENT_NAME_KEY = "document_name"
    INPUT_DIRECTORY_KEY = "input_directory"
    USE_EXTERNAL_LLM_KEY = "use_external_llm"
    APP_MODE_KEY = "app_mode"
    DEBUG_APP_MODE = "DEBUG"
    DEFAULT_FIELDS: dict[str, Any] = {USE_EXTERNAL_LLM_KEY: False, APP_MODE_KEY: DEBUG_APP_MODE}
    PATH_FIELD_NAMES = (
        "input_directory",
        "output_directory",
        "prompts_directory",
        *CommandLineArguments.PROMPT_NAMES,
    )

    def __init__(
        self,
        document_selector: BatchDocumentSelector,
        project_root_directory: Path,
    ) -> None:
        """Store the document selector and the directory that relative paths resolve against."""
        self._document_selector = document_selector
        self._project_root_directory = project_root_directory

    def read(self, batch_file_path: Path) -> BatchPlan:
        """Return the batch plan, failing when the file has no run or a run is misconfigured."""
        with batch_file_path.open("rb") as batch_file:
            batch_settings = load(batch_file)
        run_tables = batch_settings.get(self.RUN_TABLE_ARRAY_KEY, [])
        if not isinstance(run_tables, list) or not run_tables:
            raise ValueError(f"{batch_file_path} needs at least one [[run]] table")
        batch_table = batch_settings.get(self.BATCH_TABLE_KEY, {})
        if self.NAME_KEY in batch_table:
            raise ValueError(
                f"[{self.BATCH_TABLE_KEY}] must not set {self.NAME_KEY!r}; "
                f"{self.NAME_KEY!r} belongs to each [[{self.RUN_TABLE_ARRAY_KEY}]] table"
            )
        runs = tuple(
            self._build_run(run_index, run_table, batch_table)
            for run_index, run_table in enumerate(run_tables, start=1)
        )
        return BatchPlan(runs=runs)

    def _build_run(
        self,
        run_index: int,
        run_table: dict[str, Any],
        batch_table: dict[str, Any],
    ) -> BatchRun:
        """Return the run with the arguments of each document its documents select."""
        if self.NAME_KEY not in run_table:
            raise ValueError(f"run number {run_index} has no {self.NAME_KEY}")
        name = run_table[self.NAME_KEY]
        fields = self._effective_fields(name, run_table, batch_table)
        document_names = self._document_selector.select(
            fields[self.INPUT_DIRECTORY_KEY],
            run_table.get(self.DOCUMENTS_KEY, batch_table.get(self.DOCUMENTS_KEY)),
        )
        return BatchRun(
            name=name,
            document_arguments=self._document_arguments(name, fields, document_names),
        )

    def _document_arguments(
        self,
        name: str,
        fields: dict[str, Any],
        document_names: tuple[str, ...],
    ) -> tuple[CommandLineArguments, ...]:
        """Return the command line arguments of each document, naming the run on an unknown field."""
        try:
            return tuple(
                CommandLineArguments(document_name=document_name, **fields)
                for document_name in document_names
            )
        except TypeError as error:
            raise ValueError(
                f"run {name!r} has a setting that is not a command line argument: {error}"
            ) from error

    def _effective_fields(
        self,
        name: str,
        run_table: dict[str, Any],
        batch_table: dict[str, Any],
    ) -> dict[str, Any]:
        """Return the command line fields of a run: defaults, then batch, then run overrides."""
        batch_fields = {
            key: value for key, value in batch_table.items() if key != self.DOCUMENTS_KEY
        }
        run_fields = {
            key: value
            for key, value in run_table.items()
            if key not in (self.NAME_KEY, self.DOCUMENTS_KEY)
        }
        fields = {**self.DEFAULT_FIELDS, **batch_fields, **run_fields}
        if self.DOCUMENT_NAME_KEY in fields:
            raise ValueError(
                f"run {name!r} sets {self.DOCUMENT_NAME_KEY!r}; "
                f"its documents come from {self.DOCUMENTS_KEY!r}"
            )
        if self.INPUT_DIRECTORY_KEY not in fields:
            raise ValueError(f"run {name!r} has no {self.INPUT_DIRECTORY_KEY}")
        use_external_llm = fields[self.USE_EXTERNAL_LLM_KEY]
        if not isinstance(use_external_llm, bool):
            raise ValueError(
                f"run {name!r} sets {self.USE_EXTERNAL_LLM_KEY!r} to {use_external_llm!r}; "
                "it must be true or false"
            )
        if use_external_llm and not self._is_debug_app_mode(fields):
            raise ValueError(
                f"run {name!r} uses the external LLM, which needs "
                f'{self.APP_MODE_KEY} = "{self.DEBUG_APP_MODE}", but the run sets '
                f"{self.APP_MODE_KEY} = {fields[self.APP_MODE_KEY]!r}; "
                "otherwise the environment silently falls back to Ollama"
            )
        for field_name in self.PATH_FIELD_NAMES:
            if field_name in fields:
                fields[field_name] = self._resolve_path(fields[field_name])
        return fields

    def _is_debug_app_mode(self, fields: dict[str, Any]) -> bool:
        app_mode = fields.get(self.APP_MODE_KEY)
        return isinstance(app_mode, str) and app_mode.strip().upper() == self.DEBUG_APP_MODE

    def _resolve_path(self, path_text: str) -> Path:
        path = Path(path_text)
        return path if path.is_absolute() else self._project_root_directory / path
