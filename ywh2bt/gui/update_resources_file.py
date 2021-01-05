"""Models and functions used for resources updates."""
import os
import sys
from pathlib import Path
from string import Template
from typing import Generator

resources_file_template_contents = """<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource>
        ${glued_lines}
    </qresource>
</RCC>
"""
resources_file_template = Template(resources_file_template_contents)

resources_file_line_template = Template(
    '<file>${path}</file>',
)
resources_file_line_glue = '\n        '


def update() -> None:
    """Create or update the contents of resources.qrc based on the directory listing of ./resources/."""
    base_dir = os.path.dirname(__file__)
    content = _make_file_content(
        base_dir=base_dir,
    )
    file_path = f'{base_dir}/resources.qrc'
    with open(file_path, 'w') as f:
        f.write(content)
    sys.stdout.write(f'{file_path} updated.')
    sys.stdout.write('\n')


def _make_file_content(
    base_dir: str,
) -> str:
    resources_dir = 'resources'
    resources = _find_resources(
        base_dir=os.path.join(
            base_dir,
            resources_dir,
        ),
    )
    lines = map(
        lambda path: resources_file_line_template.substitute(
            path=f'{resources_dir}/{path}',
        ),
        resources,
    )
    return resources_file_template.substitute(
        glued_lines=resources_file_line_glue.join(lines),
    )


def _find_resources(
    base_dir: str,
) -> Generator[str, None, None]:
    for path in Path(base_dir).rglob('*'):
        if not path.is_file():
            continue
        yield str(path.relative_to(base_dir))


if __name__ == '__main__':
    update()
