from collections.abc import Callable


class DocumentNamePrompter:
    """Ask the user on the console for the name of the document to analyze."""

    PROMPT_TEXT = "Ingrese el nombre del documento (.docx): "

    def __init__(self, input_function: Callable[[str], str] = input) -> None:
        """Keep the function used to read the answer from the console."""
        self._input_function = input_function

    def ask(self) -> str:
        """Return the typed document name without surrounding whitespace or double quotes."""
        answer = self._input_function(self.PROMPT_TEXT)
        return answer.strip().strip('"').strip()
