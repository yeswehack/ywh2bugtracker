"""Models and functions used for JSON schema."""
import json
from functools import partial
from string import Template
from typing import Any, Callable, Dict, List

from ywh2bt.core.schema.error import SchemaError
from ywh2bt.core.schema.json import root_configuration_as_json_schema

Json = Dict[str, Any]


def root_configuration_as_text() -> str:
    """
    Get a text schema for RootConfiguration.

    Raises:
        SchemaError: if an error occurred during the creation of the schema

    Returns:
        the schema
    """
    json_schema_str = root_configuration_as_json_schema()
    try:
        schema: Json = json.loads(json_schema_str)
    except TypeError as load_error:
        raise SchemaError('JSON load error') from load_error
    return '\n'.join(
        _schema_to_str(
            schema=schema,
        ),
    )


def _schema_to_str(
    schema: Json,
) -> List[str]:
    ref = schema.get('$ref')
    if ref:
        return [
            f'Reference: {ref.replace("#/definitions/", "")}',
        ]
    any_of = schema.get('anyOf')
    if any_of:
        return _extract_any_of(
            any_of=any_of,
        )
    output = _extract_attributes(
        schema=schema,
        attributes={
            'title': 'Title',
            'description': 'Description',
            'type': 'Type',
            'const': 'Required constant value',
            'default': 'Default value',
        },
    )
    output.extend(
        _extract_properties(
            schema=schema,
        ),
    )
    output.extend(
        _extract_properties_patterns(
            schema=schema,
        ),
    )
    output.extend(
        _extract_definitions(
            schema=schema,
        ),
    )
    output.extend(
        _extract_items(
            schema=schema,
        ),
    )

    return output


def _extract_attributes(
    schema: Json,
    attributes: Dict[str, str],
) -> List[str]:
    output = []
    for attribute, label in attributes.items():
        value = schema.get(attribute)
        if value is not None:
            output.append(f'{label}: {value}')
    return output


def _extract_properties(
    schema: Json,
) -> List[str]:
    required = schema.get('required', [])
    properties = []
    for property_name, property_schema in schema.get('properties', {}).items():
        properties.append(f'- {property_name}')
        properties.extend(
            _prefix_lines(
                '  ',
                _schema_to_str(
                    schema=property_schema,
                ),
            ),
        )
        if property_name in required:
            properties.append('  Required: True')
    if not properties:
        return []
    return [
        'Properties:',
        *_prefix_lines(
            '  ',
            properties,
        ),
    ]


def _extract_properties_patterns(
    schema: Json,
) -> List[str]:
    return _extract_list(
        schema=schema,
        attribute_name='patternProperties',
        block_label='Properties patterns:',
        item_name_template=Template('- Pattern: ${item_name}'),
    )


def _extract_definitions(
    schema: Json,
) -> List[str]:
    return _extract_list(
        schema=schema,
        attribute_name='definitions',
        block_label='Definitions:',
        item_name_template=Template('${item_name}:'),
    )


def _extract_items(
    schema: Json,
) -> List[str]:
    items = schema.get('items')
    if not items:
        return []
    return [
        'Items:',
        *_prefix_lines(
            '  ',
            _schema_to_str(
                schema=items,
            ),
        ),
    ]


def _extract_list(
    schema: Json,
    attribute_name: str,
    block_label: str,
    item_name_template: Template,
) -> List[str]:
    items = []
    for item_name, item_schema in schema.get(attribute_name, {}).items():
        items.append(item_name_template.substitute(item_name=item_name))
        items.extend(
            _prefix_lines(
                '  ',
                _schema_to_str(
                    schema=item_schema,
                ),
            ),
        )
    if not items:
        return []
    return [
        block_label,
        *_prefix_lines(
            '  ',
            items,
        ),
    ]


def _extract_any_of(
    any_of: List[Json],
) -> List[str]:
    output = [
        'Any of:',
    ]
    for any_of_entry in any_of:
        output.extend(
            _prefix_lines(
                '  - ',
                list(_schema_to_str(
                    schema=any_of_entry,
                )),
            ),
        )
    return output


def _prefix(
    prefix: str,
    string: str,
) -> str:
    return f'{prefix}{string}'


def _prefix_lines(
    prefix: str,
    lines: List[str],
) -> List[str]:
    return list(map(
        _prefixer(prefix),
        lines,
    ))


def _prefixer(
    prefix: str,
) -> Callable[[str], str]:
    return partial(
        _prefix,
        prefix,
    )
