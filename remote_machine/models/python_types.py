from dataclasses import dataclass


@dataclass(frozen=True)
class PythonResult:
    version: str
    venv_path: str
    result: str
