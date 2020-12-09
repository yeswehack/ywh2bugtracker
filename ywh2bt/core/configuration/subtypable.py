"""Models and functions used in class subtyping and automatic casting."""
from __future__ import annotations

from abc import ABCMeta
from typing import Any, Dict, Optional, Tuple, Type, cast

from ywh2bt.core.configuration.error import BaseAttributeError

SUBTYPE_MANAGER_ATTR_NAME = '__subtype_manager'


class SubtypeError(BaseAttributeError):
    """An error related to a subtype."""


class Subtypable:
    """Base class for all subtypes."""


class SubtypableMetaclass(ABCMeta):
    """
    A metaclass for subtypes.

    Used to determine a subtype class from a string type.

    Examples:
        class CustomType(Subtypable):
            pass

        SubtypableMetaclass.register_subtype('custom-type', CustomType)
        instance = Subtypable(type='custom-type')
        assert isinstance(instance, CustomType)  # => True

    """

    def _get_subtype_manager(
        cls,
    ) -> SubtypableManager:
        return cast(
            SubtypableManager,
            getattr(cls, SUBTYPE_MANAGER_ATTR_NAME),
        )

    def get_registered_subtypes(
        cls,
    ) -> Dict[str, Type[Subtypable]]:
        """
        Get the registered subtypes.

        Returns:
            the registered subtypes
        """
        return cls._get_subtype_manager().get_registered_subtypes()

    def register_subtype(
        cls,
        subtype_name: str,
        subtype_class: Type[Subtypable],
    ) -> None:
        """
        Associate a type name with a subtype class.

        Args:
            subtype_name: the type name
            subtype_class: the subtype class

        # noqa: DAR101 mcs
        """
        cls._get_subtype_manager().register_subtype(
            subtype_name=subtype_name,
            subtype_class=subtype_class,
        )

    def get_subtype_name(
        cls,
        subtype_class: Type[Any],
    ) -> Optional[str]:
        """
        Get a subtype class from a type name.

        Args:
            subtype_class: a type name

        Returns:
            A subtype class

        # noqa: DAR101 mcs
        """
        return cls._get_subtype_manager().get_subtype_name(
            subtype_class=subtype_class,
        )

    def __new__(
        mcs,
        name: str,
        bases: Tuple[Type[Any], ...],
        namespace: Dict[str, Any],
    ) -> SubtypableMetaclass:
        """
        Call to create a new subtype class of class cls.

        Args:
            name: a name for the new class
            bases: class bases for the new class
            namespace: properties and attributes of the new class

        Returns:
            The new class
        """
        if Subtypable in bases:
            subtype_manager = SubtypableManager()
            namespace[SUBTYPE_MANAGER_ATTR_NAME] = subtype_manager

        return super(SubtypableMetaclass, mcs).__new__(mcs, name, bases, namespace)  # type: ignore  # noqa: WPS608

    def __call__(
        cls,
        *args: Any,
        **kwargs: Any,
    ) -> Subtypable:
        """
        Call the subtypable type as a function.

        Shorthand for `Subtypable.__call__(*args, **kwargs)`.

        Args:
            args: an arguments list
            kwargs: keyword arguments

        Raises:
            SubtypeError: if the subtype is not found in the registered subtypes

        Returns:
            A subtype instance

        # noqa: DAR101 cls
        """
        new_cls = cls
        subtypes = getattr(cls, 'get_registered_subtypes')()  # noqa: B009
        if Subtypable in cls.__bases__:
            subtype_name = kwargs.pop('type', None)
            if subtype_name:
                if subtype_name in subtypes:
                    new_cls = subtypes[subtype_name]  # noqa: WPS529
                else:
                    raise SubtypeError(
                        message=f'Subtype {repr(subtype_name)} is not supported.',
                        context=None,
                    )
            else:
                raise SubtypeError(
                    message='No subtype provided.',
                    context=None,
                )
        obj = cls.__new__(new_cls, *args, **kwargs)  # type: ignore
        obj.__init__(*args, **kwargs)  # type: ignore  # noqa: WPS609
        return cast(Subtypable, obj)


class SubtypableManager:
    """A class for handling the subclasses of a subtypable class."""

    _subtypes: Dict[str, Type[Subtypable]]

    def __init__(
        self,
    ) -> None:
        """Initialize self."""
        self._subtypes = {}

    def get_registered_subtypes(
        self,
    ) -> Dict[str, Type[Subtypable]]:
        """
        Get the registered subtypes.

        Returns:
            the registered subtypes
        """
        return self._subtypes.copy()

    def register_subtype(
        self,
        subtype_name: str,
        subtype_class: Type[Subtypable],
    ) -> None:
        """
        Associate a type name with a subtype class.

        Args:
            subtype_name: the type name
            subtype_class: the subtype class

        Raises:
            SubtypeError: if the class is not a subclass of Subtypable

        # noqa: DAR101 mcs
        """
        if not issubclass(subtype_class, Subtypable):
            raise SubtypeError(
                message=f'Class {subtype_class} is not a subclass of {Subtypable}.',
                context=None,
            )
        self._subtypes[subtype_name] = subtype_class

    def get_subtype_name(
        self,
        subtype_class: Type[Any],
    ) -> Optional[str]:
        """
        Get a subtype class from a type name.

        Args:
            subtype_class: a type name

        Returns:
            A subtype class

        # noqa: DAR101 mcs
        """
        for registered_name, registered_class in self._subtypes.items():
            if registered_class is subtype_class:
                return registered_name
        return None
