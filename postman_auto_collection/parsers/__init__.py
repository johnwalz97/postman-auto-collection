from typing import Protocol

from . import fastapi


class Parser(Protocol):
    def parse(self, file_path: str) -> str:
        ...


__all__ = ["fastapi", "Parser"]
