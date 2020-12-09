"""Models and functions used for schema."""
from typing_extensions import Protocol


class SchemaDumpProtocol(Protocol):
    """Protocol for schema dump."""

    def __call__(
        self,
    ) -> str:
        """Dump the schema."""
        ...  # noqa: WPS428
