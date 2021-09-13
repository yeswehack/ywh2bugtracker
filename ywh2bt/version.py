"""Version."""
import os

import pkg_resources
import tomlkit

try:
    __VERSION__ = pkg_resources.get_distribution('ywh2bt').version
except pkg_resources.DistributionNotFound:
    # fallback if project is not installed
    pyproject_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'pyproject.toml',
    )
    with open(pyproject_path) as pyproject_file:
        pyproject = pyproject_file.read()
    __VERSION__ = 'Unknown'
    tool = tomlkit.api.parse(pyproject).get('tool')
    if tool:
        poetry = tool.get('poetry')
        if poetry:
            __VERSION__ = poetry.get('version', 'Unknown')
