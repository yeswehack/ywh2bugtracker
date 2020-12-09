from __future__ import annotations

import io
import sys
from types import TracebackType
from typing import Dict, List, Type


class StdRedirect:
    _new_targets: Dict[str, io.StringIO]
    _old_targets: Dict[str, List[io.StringIO]]

    def __init__(self) -> None:
        self._new_targets = {
            'stdout': io.StringIO(),
            'stderr': io.StringIO(),
        }
        self._old_targets = {
            'stdout': [],
            'stderr': [],
        }

    def __enter__(self) -> StdRedirect:
        for stream_name, new_target in self._new_targets.items():
            self._old_targets[stream_name].append(getattr(sys, stream_name))
            setattr(sys, stream_name, new_target)
        return self

    def __exit__(
        self,
        exc_type: Type[SystemExit],
        exc_inst: SystemExit,
        exc_tb: TracebackType,
    ) -> None:
        for stream_name, old_targets in self._old_targets.items():
            setattr(sys, stream_name, old_targets.pop())

    def _get_value(
        self,
        stream_name: str,
    ) -> str:
        return self._new_targets[stream_name].getvalue()

    def get_stdout(self) -> str:
        return self._get_value('stdout')

    def get_stderr(self) -> str:
        return self._get_value('stderr')

    @classmethod
    def redirect(cls) -> StdRedirect:
        return StdRedirect()
