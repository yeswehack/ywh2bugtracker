from typing import (
    Any,
    Tuple,
)


class FileHandler:
    file_path: Any = ...
    file: Any = ...
    open: bool = ...

    def __init__(self, file_name: str, dir_path: str = ...) -> None: ...

    def read(self) -> bytes: ...

    def write(self, data: bytes) -> None: ...

    def __enter__(self) -> FileHandler: ...

    def __exit__(self, *_: Tuple[Any, ...]) -> None: ...


class FileWriter(FileHandler):
    bytes_written: int

    def write(self, data: bytes) -> None: ...

    def read(self) -> bytes: ...


class FileReader(FileHandler):
    def read(self) -> bytes: ...

    def write(self, data: bytes) -> None: ...
