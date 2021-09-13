"""Models and functions used for configuration definitions."""
from __future__ import annotations

from collections import OrderedDict
from typing import (  # noqa: WPS235
    Any,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    OrderedDict as OrderedDictType,
    Text,
    Type,
    TypeVar,
    Union,
    cast,
)

from ywh2bt.core.configuration.error import (
    AttributesError,
    BaseAttributeError,
    InvalidAttributeError,
    MissingAttributeError,
    UnsupportedAttributeError,
)
from ywh2bt.core.configuration.exportable import Exportable
from ywh2bt.core.configuration.validatable import Validatable
from ywh2bt.core.configuration.validator import ValidatorError, ValidatorProtocol

T = TypeVar('T', covariant=True)
V = TypeVar('V', covariant=True)


class Attribute(Generic[T]):  # noqa: WPS214
    """
    A class representing an attribute of a configuration.

    Examples:
        class MyContainer(AttributesContainer):
            my_string_attribute = Attribute.create(value_type='str')

        instance = MyContainer()
        instance.my_string_attribute = 'foo'
        print(instance.my_string_attribute)
    """

    _name: Optional[str] = None
    value_type: Type[T]
    secret: bool
    required: bool
    default: Optional[T]
    deprecated: bool
    short_description: Optional[Text] = None
    description: Optional[Text] = None
    validator: Optional[ValidatorProtocol[T]] = None

    def __init__(
        self,
        value_type: Type[T],
        short_description: Optional[Text] = None,
        description: Optional[Text] = None,
        default: Optional[T] = None,
        secret: bool = False,
        required: bool = False,
        deprecated: bool = False,
        validator: Optional[ValidatorProtocol[T]] = None,
    ) -> None:
        """
        Initialize the attribute.

        Args:
            value_type: a type expected for the value of the attribute
            short_description: a short description of the attribute
            description: a description of the attribute
            default: a default value for the attribute
            secret: a flag indicating if the attribute is secret (avoid representing/printing sensible data)
            required: a flag indicating if the attribute must have a non-None value
            deprecated: a flag indicating if the attribute is deprecated
            validator: a function validating the value of the attribute

        Raises:
            InvalidAttributeError: if the attribute could not be initialized
        """
        self.value_type = value_type
        self.short_description = short_description
        self.description = description
        self.secret = secret
        self.required = required
        self.deprecated = deprecated
        self.default = default
        self.validator = validator
        if default is not None:
            self._ensure_default_value_type()
            if validator:
                try:
                    validator(
                        value=default,
                    )
                except ValidatorError as e:
                    raise InvalidAttributeError(
                        message=f'Validation error for default value ({repr(default)}): {e}',
                        context=self,
                    )

    @classmethod
    def create(
        cls,
        value_type: Type[V],
        short_description: Optional[Text] = None,
        description: Optional[Text] = None,
        default: Optional[V] = None,
        secret: bool = False,
        required: bool = False,
        deprecated: bool = False,
        validator: Optional[ValidatorProtocol[V]] = None,
    ) -> Attribute[V]:
        """
        Create a new attribute.

        Must only be used in the definition of classes extending `AttributesContainer`.

        Args:
            value_type: a type expected for the value of the attribute
            short_description: a short description of the attribute
            description: a description of the attribute
            default: a default value for the attribute
            secret: a flag indicating if the attribute is secret (avoid representing/printing sensible data)
            required: a flag indicating if the attribute must have a non-None value
            deprecated: a flag indicating if the attribute is deprecated
            validator: a function validating the value of the attribute

        Returns:
            The newly created attribute
        """
        return Attribute[V](
            value_type=value_type,
            short_description=short_description,
            description=description,
            default=default,
            secret=secret,
            required=required,
            deprecated=deprecated,
            validator=validator,
        )

    def validate(
        self,
        value: Any,
    ) -> None:
        """
        Validate a possible value for the attribute.

        Args:
            value: a value to be validated
        """
        if value is None:
            self._ensure_required_has_default()
            value = self.default
        if value is not None:
            self._ensure_value_type(value=value)
            self._ensure_validity(value=value)

    def __set__(
        self,
        instance: AttributesContainer,
        value: Any,
    ) -> None:
        """
        Set the value of a descriptor.

        Is called to set the attribute on an instance `instance` of the owner class to a new value, `value`.

        Args:
            instance: an instance of the owner class
            value: a value

        Returns:
            None
        """
        if value:
            if isinstance(value, Dict):
                value = self.value_type(**value)  # type: ignore
            elif isinstance(value, List):
                value = self.value_type(value)  # type: ignore
        return instance.set_attribute_value(
            attribute=self,
            value=value,
        )

    def __get__(
        self,
        instance: AttributesContainer,
        owner: Type[AttributesContainer],
    ) -> Optional[T]:
        """
        Get a computed value of a descriptor.

        Is called to get the attribute of the owner class (class attribute access)
        or of an instance of that class (instance attribute access).

        Args:
            instance: instance that the attribute was accessed through
            owner: owner class

        Returns:
            The computed value
        """
        return cast(Optional[T], instance.get_attribute_value(
            attribute=self,
        )) if instance is not None else self

    def __set_name__(
        self,
        owner: Type[AttributesContainer],
        name: str,
    ) -> None:
        """
        Is called at the time the owning class `owner` is created.

        Args:
            owner: owner class
            name: a descriptor name
        """
        self._name = name

    @property
    def name(self) -> str:
        """
        Get the name of the attribute.

        Returns:
            The name of the attribute
        """
        if self._name is not None:
            return self._name
        return f'Unnamed attribute #{hash(self):x}'

    def as_repr(
        self,
        value: Optional[T],
    ) -> str:
        """
        Get a safe string representation of the value depending on the `secret` flag.

        Args:
            value: a value to be represented

        Returns:
            The safe string representation
        """
        if value is not None and self.secret:
            return f"<secret-{self.value_type.__name__} '***'>"
        return repr(value)

    def __repr__(self) -> str:
        """
        Is called by the `repr()` built-in function to compute the "official" string representation.

        Returns:
            The string representation
        """
        items = [
            f'name={repr(self.name)}',
            f'value_type={repr(self.value_type)}',
            f'required={repr(self.required)}',
            f'secret={repr(self.secret)}',
        ]
        if self.short_description:
            items.append(f'short_description={repr(self.short_description)}')
        if self.description:
            items.append(f'description={repr(self.description)}')
        if self.default is not None:
            items.append(f'default={self.as_repr(self.default)}')

        joined_items = ', '.join(items)
        return f'{self.__class__.__name__}({joined_items})'

    def _ensure_default_value_type(self) -> None:
        if not isinstance(self.default, self.value_type):
            default_type = type(self.default)
            safe_default_repr = self.as_repr(self.default)
            message = f'Expecting {self.value_type} for default value ; got {default_type} ({safe_default_repr}).'
            raise InvalidAttributeError(
                message=message,
                context=self,
            )

    def _ensure_required_has_default(self) -> None:
        if self.default is None:
            if self.required:
                raise MissingAttributeError(
                    message=f'Expecting value for required attribute {repr(self.name)} with no default',
                    context=self,
                )

    def _ensure_value_type(
        self,
        value: Any,
    ) -> None:
        if not isinstance(value, self.value_type):
            name_repr = repr(self.name)
            if self.short_description:
                name_repr = f'{self.short_description} ; {name_repr}'
            value_type = type(value)
            safe_value_repr = self.as_repr(value)
            message = (
                f'Wrong value type for {name_repr} = {safe_value_repr}: expecting {self.value_type} got {value_type}'
            )
            raise InvalidAttributeError(
                message=message,
                context=self,
            )

    def _ensure_validity(
        self,
        value: Any,
    ) -> None:
        if isinstance(value, Validatable):
            value.validate()
        if self.validator:
            self.apply_validator(
                validator=self.validator,
                value=value,
            )

    def apply_validator(
        self,
        validator: ValidatorProtocol[T],
        value: Any,
    ) -> None:
        """
        Apply the validator to the given value.

        Args:
            validator: a validator
            value: a value

        Raises:
            InvalidAttributeError: if the attribute value is invalid
        """
        try:
            validator(
                value=value,
            )
        except ValidatorError as e:
            name_repr = repr(self.name)
            if self.short_description:
                name_repr = f'{self.short_description} ; {name_repr}'
            safe_value_repr = self.as_repr(value)
            message = f'Validation error for {name_repr} = {safe_value_repr}: {e}'
            raise InvalidAttributeError(
                message=message,
                context=self,
            )


class AttributesContainer(
    Validatable,
    Exportable[Dict[str, Any]],
):
    """A class representing a container for all the attributes of a configuration."""

    _values: Dict[Attribute[Any], Any]
    _extra: Dict[str, Any]

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the container.

        Args:
            kwargs: keyword arguments
        """
        self._values = {}
        for _, value in self.get_attributes().items():
            if isinstance(value, Attribute):
                self._values[value] = None
        self._extra = kwargs or {}

    @classmethod
    def get_attributes(cls) -> Dict[str, Attribute[Any]]:
        """
        Get all created attributes.

        Returns:
            The attributes
        """
        attributes = OrderedDict()
        for name, value in vars(cls).items():  # noqa: WPS421
            if isinstance(value, Attribute):
                attributes[name] = value
        return attributes

    def set_attribute_value(
        self,
        attribute: Attribute[Any],
        value: Any,
    ) -> None:
        """
        Set the value of an attribute.

        Args:
            attribute: an attribute
            value: a value
        """
        self._values[attribute] = value

    def get_attribute_value(
        self,
        attribute: Attribute[Any],
    ) -> Any:
        """
        Get the value of an attribute.

        Args:
            attribute: an attribute

        Returns:
            The attribute value
        """
        value = self._values[attribute] if attribute in self._values else attribute.default
        return value if value is not None else attribute.default

    def validate(self) -> None:
        """
        Validate the container.

        Raises:
            AttributesError: if the container is not valid
        """
        errors: Dict[str, BaseAttributeError] = {}
        for attribute, value in self._values.items():
            try:
                attribute.validate(
                    value=value,
                )
            except BaseAttributeError as e:
                errors[attribute.name] = e
        for extra_key, _ in self._extra.items():
            errors[extra_key] = UnsupportedAttributeError(
                message='Unsupported attribute',
                context=self,
            )
        if errors:
            raise AttributesError(
                message='Validation failed',
                errors=errors,
                context=self,
            )

    def export(self) -> Dict[str, Any]:
        """
        Export the container values as a dictionary.

        Returns:
            The exported values
        """
        values: Dict[str, Any] = {}
        for attribute, value in self._values.items():
            if isinstance(value, Exportable):
                exported = value.export()
                if exported is not None:
                    values[attribute.name] = exported
            elif value is not None:
                values[attribute.name] = value
        values.update(self._extra)
        return values

    def __str__(self) -> str:
        """
        Get the string value.

        Is called by `str(object)` and the built-in functions `format()` and `print()`
        to compute the "informal" or nicely printable string representation.

        Returns:
            The string value
        """
        joined_items = ', '.join([
            f'{attr.name}={attr.as_repr(value=self.get_attribute_value(attribute=attr))}'  # noqa: WPS221
            for attr, value in self._values.items()
        ])
        return f'{self.__class__.__name__}({joined_items})'

    def __repr__(self) -> str:
        """
        Is called by the `repr()` built-in function to compute the "official" string representation.

        Returns:
            The string representation
        """
        return self.__str__()


T_AC = TypeVar('T_AC', bound=AttributesContainer)


class AttributesContainerList(
    List[T_AC],
    Validatable,
    Exportable[List[Any]],
):
    """A class representing a typed list of attributes container."""

    values_type: Type[T_AC]

    def __init__(
        self,
        values_type: Type[T_AC],
        items: Optional[List[T_AC]],
    ):
        """
        Initialize the list.

        Args:
            values_type: a type for the items of the list
            items: initial items to be added to the list
        """
        new_seq: List[T_AC] = []
        if items:
            for item in items:
                if isinstance(item, values_type):
                    new_seq.append(item)
                elif item is not None:
                    new_seq.append(values_type(**item))  # type: ignore
        super().__init__(new_seq)
        self.values_type = values_type

    def append(self, obj: Optional[T_AC]) -> None:
        """
        Append an item to the list.

        This also tries to cast the value to the relevant type if the value is not an instance of the expected type.

        Args:
            obj: a item to be appended
        """
        if obj is not None:
            super().append(
                obj
                if isinstance(obj, self.values_type)
                else self.values_type(**obj),  # type: ignore
            )

    def validate(self) -> None:
        """
        Validate the list.

        Raises:
            AttributesError: if the list is not valid
        """
        errors: Dict[str, BaseAttributeError] = {}
        for i, item in enumerate(self):
            if not isinstance(item, self.values_type):
                item_type = type(item)
                item_repr = repr(item)
                errors[str(i)] = InvalidAttributeError(
                    message=(
                        f'Expecting {self.values_type} for item {i} ; '
                        + f'got {item_type} ({item_repr})'
                    ),
                    context=self,
                )
            elif isinstance(item, Validatable):
                try:
                    item.validate()
                except BaseAttributeError as e:
                    errors[str(i)] = e
        if errors:
            raise AttributesError(
                message='Validation failed',
                errors=errors,
                context=self,
            )

    def export(self) -> List[Any]:
        """
        Export the list.

        Returns:
            The exported values
        """
        values: List[Any] = []
        for container in self:
            if isinstance(container, Exportable):
                values.append(container.export())
            elif container is not None:
                values.append(container)
        return values


KT = TypeVar('KT')
VT = TypeVar('VT')
EKT = TypeVar('EKT')
EVT = TypeVar('EVT')


class ExportableDict(OrderedDictType[KT, VT], Exportable[Dict[EKT, EVT]]):
    """A class describing an exportable dict."""

    def export(self) -> Dict[EKT, EVT]:
        """
        Export the dict.

        Returns:
            the exported dict
        """
        return dict(self)  # type: ignore

    def swap_key(
        self,
        old: KT,
        new: KT,
    ) -> None:
        """
        Swap item key.

        Args:
            old: an old key
            new: a new key
        """
        for _ in range(len(self)):  # noqa: WPS122, WPS518
            k, v = self.popitem(False)
            self[new if old == k else k] = v


class AttributesContainerDict(
    ExportableDict[str, T_AC, str, Any],
    Validatable,
):
    """A class representing dictionary of attributes container."""

    values_type: Type[T_AC]

    def __init__(
        self,
        values_type: Type[T_AC],
        items: Mapping[str, Any],
    ) -> None:
        """
        Initialize the dictionary.

        Args:
            values_type: a type for the items of the dict
            items: initial items to be added to the dict

        Raises:
            AttributesError: if an item is invalid
        """
        self.values_type = values_type
        errors = {}
        new_items: Dict[str, T_AC] = {}
        for key, item in items.items():
            try:
                if isinstance(item, values_type):
                    new_items[key] = item
                elif item is not None:
                    new_items[key] = self._init_item(
                        item=item,
                    )
            except BaseAttributeError as e:
                errors[key] = e
        if errors:
            raise AttributesError(
                message='Invalid items',
                context=self,
                errors=errors,
            )
        super().__init__(new_items)

    def _init_item(
        self,
        item: Any,
    ) -> T_AC:
        return self.values_type(**item)

    def validate(self) -> None:
        """
        Validate the dictionary.

        Raises:
            AttributesError: if the list is not valid
        """
        errors: Dict[str, BaseAttributeError] = {}
        for key, container in self.items():
            try:
                container.validate()
            except BaseAttributeError as e:
                errors[key] = e
        if errors:
            raise AttributesError(
                message='Validation failed',
                errors=errors,
                context=self,
            )

    def export(self) -> Dict[str, Any]:
        """
        Export the dictionary.

        Returns:
            The exported values
        """
        values: Dict[str, Any] = {}
        for key, container in self.items():
            if isinstance(container, Exportable):
                values[key] = container.export()
            elif container is not None:
                values[key] = container
        return values


StrAttributeType = Union[Optional[str], Attribute[str]]
BoolAttributeType = Union[Optional[bool], Attribute[bool]]

ET = TypeVar('ET')


class ExportableList(List[T], Exportable[List[ET]]):
    """A list."""

    def export(self) -> List[ET]:
        """
        Export the list.

        Returns:
            the exported list
        """
        return cast(List[ET], self.copy())
