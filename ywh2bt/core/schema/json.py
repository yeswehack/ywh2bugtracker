"""Models and functions used for JSON schema."""
import json
from io import StringIO
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Type

from typing_extensions import Protocol

from ywh2bt.core.configuration.attribute import (
    Attribute,
    AttributesContainer,
    AttributesContainerDict,
    AttributesContainerList,
    ExportableDict,
    ExportableList,
)
from ywh2bt.core.configuration.root import RootConfiguration
from ywh2bt.core.configuration.subtypable import SubtypableMetaclass
from ywh2bt.core.schema.error import SchemaError

Json = Dict[str, Any]


def root_configuration_as_json_schema() -> str:
    """
    Get a JSON schema for RootConfiguration.

    Raises:
        SchemaError: if an error occurred during the creation of the schema

    Returns:
        the JSON schema
    """
    schema = _root_configuration_to_schema()
    stream = StringIO()
    try:
        json.dump(
            schema,
            fp=stream,
            indent=2,
        )
    except TypeError as dump_error:
        raise SchemaError('JSON dump error') from dump_error
    return stream.getvalue()


def _root_configuration_to_schema() -> Json:
    schema = {
        '$schema': 'http://json-schema.org/draft-07/schema',
        'title': 'Root configuration',
        'description': 'Root configuration for ywh2bt synchronization',
        'definitions': {},
    }
    schema.update(
        _attributes_container_to_schema(
            root_schema=schema,
            attribute=Attribute.create(
                value_type=RootConfiguration,
            ),
            as_ref=False,
        ),
    )
    return schema


def _attribute_to_schema(
    root_schema: Json,
    attribute: Attribute[Any],
    extra_properties: Optional[Json] = None,
) -> Json:
    value_type = attribute.value_type
    for known_type, protocol in type_to_schema_protocols.items():
        if issubclass(value_type, known_type):
            return protocol(
                root_schema=root_schema,
                attribute=attribute,
                extra_properties=extra_properties,
                as_ref=True,
            )
    raise SchemaError(f'Unhandled {repr(value_type.__name__)}')


def _attribute_to_base_schema(
    attribute: Attribute[Any],
) -> Json:
    schema = {}
    if attribute.short_description:
        schema['title'] = attribute.short_description
    if attribute.description:
        schema['description'] = attribute.description
    if attribute.deprecated:
        description = schema.get('description')
        if description:
            schema['description'] = f'(Deprecated)\n{description}'
        else:
            schema['description'] = '(Deprecated)'
    if attribute.default is not None:
        schema['default'] = attribute.default
    return schema


def _attributes_container_to_schema(
    root_schema: Json,
    attribute: Attribute[AttributesContainer],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    required = []
    value_type = attribute.value_type
    properties = {}
    if extra_properties:
        properties.update(extra_properties)
    for name, child_attribute in value_type.get_attributes().items():
        if child_attribute.required:
            required.append(name)
        properties[child_attribute.name] = {
            **_attribute_to_base_schema(
                attribute=child_attribute,
            ),
            **_attribute_to_schema(
                root_schema=root_schema,
                attribute=child_attribute,
            ),
        }

    schema: Json = {
        'type': 'object',
    }
    if properties:
        schema['properties'] = properties
    if required:
        schema['required'] = required
    schema['additionalProperties'] = False

    if not as_ref:
        return schema

    root_schema['definitions'][value_type.__name__] = schema
    return {
        '$ref': f'#/definitions/{value_type.__name__}',
    }


def _attribute_container_dict_to_schema(
    root_schema: Json,
    attribute: Attribute[AttributesContainerDict[Any]],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    return {
        'type': 'object',
        'patternProperties': {
            '.+': _get_pattern_properties(
                root_schema=root_schema,
                attribute=attribute,
            ),
        },
        'additionalProperties': False,
    }


def _get_pattern_properties(
    root_schema: Json,
    attribute: Attribute[Any],
) -> Json:
    value_type = attribute.value_type
    instance = value_type()
    item_values_type = instance.values_type
    if isinstance(item_values_type, SubtypableMetaclass):
        any_of = []
        for type_name, type_class in item_values_type.get_registered_subtypes().items():
            any_of.append(
                _attribute_to_schema(
                    root_schema=root_schema,
                    attribute=Attribute.create(
                        value_type=type_class,
                    ),
                    extra_properties={
                        'type': {
                            'const': type_name,
                        },
                    },
                ),
            )
        return {
            'anyOf': any_of,
        }
    return _attribute_to_schema(
        root_schema=root_schema,
        attribute=Attribute.create(
            value_type=item_values_type,
        ),
    )


def _attribute_container_list_to_schema(
    root_schema: Json,
    attribute: Attribute[AttributesContainerList[Any]],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    value_type = attribute.value_type
    instance = value_type()  # type: ignore
    item_values_type = instance.values_type
    return {
        'type': 'array',
        'items': _attribute_to_schema(
            root_schema=root_schema,
            attribute=Attribute.create(
                value_type=item_values_type,
            ),
        ),
    }


def _exportable_dict_to_schema(
    root_schema: Json,
    attribute: Attribute[ExportableDict[Any, Any, Any, Any]],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    return {
        'type': 'object',
        'patternProperties': {
            '.*': {
                'type': 'string',
            },
        },
    }


def _exportable_list_to_schema(
    root_schema: Json,
    attribute: Attribute[ExportableList[Any, Any]],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    return {
        'type': 'array',
        'items': {
            'type': 'string',
        },
    }


def _str_to_schema(
    root_schema: Json,
    attribute: Attribute[str],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    return {
        'type': 'string',
    }


def _bool_to_schema(
    root_schema: Json,
    attribute: Attribute[bool],
    extra_properties: Optional[Json] = None,
    as_ref: bool = False,
) -> Json:
    return {
        'type': 'boolean',
    }


class _ToSchemaProtocol(Protocol):

    def __call__(
        self,
        root_schema: Json,
        attribute: Attribute[Any],
        extra_properties: Optional[Json] = None,
        as_ref: bool = False,
    ) -> Json:
        ...  # noqa: WPS428


TrackerClientClassesType = Mapping[
    Type[Any],
    _ToSchemaProtocol,
]
type_to_schema_protocols: TrackerClientClassesType = MappingProxyType({
    AttributesContainer: _attributes_container_to_schema,
    AttributesContainerDict: _attribute_container_dict_to_schema,
    AttributesContainerList: _attribute_container_list_to_schema,
    ExportableDict: _exportable_dict_to_schema,
    ExportableList: _exportable_list_to_schema,
    str: _str_to_schema,
    bool: _bool_to_schema,
})
