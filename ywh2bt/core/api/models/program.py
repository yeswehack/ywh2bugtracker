from dataclasses import dataclass


@dataclass
class ProgramEmbedded:

    program_type: str
    demo: bool
    slug: str
