import os


def resource(
    path: str,
) -> str:
    return os.path.join(os.path.dirname(__file__), "resources", path)
