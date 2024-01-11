from typing import (
    List,
    Union,
)


def _sizeof_fmt(
    num: Union[int, float], base: int, units: List[str], max_unit: str, precision: int = 1, suffix: str = "B"
) -> str:
    for unit in units:
        if abs(num) < base:
            return f"{num:.{precision}f}{unit}{suffix}"
        num /= base
    return f"{num:.{precision}f}{max_unit}{suffix}"


def sizeof_fmt_iec(num: Union[int, float], precision: int = 1, suffix: str = "B") -> str:
    return _sizeof_fmt(
        num,
        base=1024,
        units=["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"],
        max_unit="Yi",
        precision=precision,
        suffix=suffix,
    )


def sizeof_fmt_si(num: Union[int, float], precision: int = 1, suffix: str = "B") -> str:
    return _sizeof_fmt(
        num,
        base=1000,
        units=["", "k", "M", "G", "T", "P", "E", "Z"],
        max_unit="Y",
        precision=precision,
        suffix=suffix,
    )
