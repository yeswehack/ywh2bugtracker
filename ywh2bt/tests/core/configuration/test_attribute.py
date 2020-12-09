import unittest
from typing import Any

from ywh2bt.core.configuration.attribute import (
    Attribute,
    AttributesContainer,
    AttributesContainerDict,
    AttributesContainerList
)
from ywh2bt.core.configuration.error import AttributesError, BaseAttributeError
from ywh2bt.core.configuration.validator import ValidatorError


class TestAttribute(unittest.TestCase):

    def test_attribute_validate_wrong_type(self) -> None:
        attr = Attribute.create(
            value_type=str,
        )
        with self.assertRaises(BaseAttributeError):
            attr.validate(value=123)

    def test_attribute_validate_required_no_default(self) -> None:
        attr = Attribute.create(
            value_type=str,
            required=True,
        )
        with self.assertRaises(BaseAttributeError):
            attr.validate(value=None)

    def test_attribute_validator_fail(self) -> None:
        def validator(value: str) -> None:  # noqa: WPS430
            raise ValidatorError()

        attr = Attribute.create(
            value_type=str,
            validator=validator,
        )
        with self.assertRaises(BaseAttributeError):
            attr.validate(value='123')

    def test_str_attribute_as_repr(self) -> None:
        attr = Attribute.create(
            value_type=str,
        )
        self.assertEqual("'my value'", attr.as_repr('my value'))

    def test_int_attribute_as_repr(self) -> None:
        attr = Attribute.create(
            value_type=int,
        )
        self.assertEqual('123', attr.as_repr(123))

    def test_attribute_as_repr_secret(self) -> None:
        attr = Attribute.create(
            value_type=str,
            secret=True,
        )
        self.assertEqual("<secret-str '***'>", attr.as_repr('my value'))


class TestAttributesContainer(unittest.TestCase):

    def test_secret(self) -> None:
        class Container(AttributesContainer):  # noqa: WPS431
            not_sec = Attribute.create(
                value_type=str,
                secret=False,
            )
            sec = Attribute.create(
                value_type=str,
                secret=True,
            )

        instance = Container()
        instance.not_sec = 'my-login'
        instance.sec = 'my-password'
        string = str(instance)
        self.assertIn('my-login', string)
        self.assertNotIn('my-password', string)

    def test_default(self) -> None:
        class Container(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
                default='default-value',
            )

        instance = Container()
        self.assertEqual('default-value', instance.field)
        instance.field = 'foo'
        self.assertEqual('foo', instance.field)
        instance.field = None
        self.assertEqual('default-value', instance.field)

    def test_validate_wrong_type(self) -> None:
        class Container(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
            )

        instance = Container()
        instance.field = 123
        with self.assertRaises(AttributesError):
            instance.validate()

    def test_validate_required_no_default(self) -> None:
        class Container(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
                required=True,
            )

        instance = Container()
        instance.field = None
        with self.assertRaises(AttributesError):
            instance.validate()

    def test_validate_required(self) -> None:
        class Container(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
                required=True,
                default='foo',
            )

        instance = Container()
        instance.field = None
        instance.validate()

    def test_validate_validator(self) -> None:
        def validator(value: str) -> None:  # noqa: WPS430
            pass

        class Container(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
                required=True,
                validator=validator,
            )

        instance = Container()
        instance.field = 'foo'
        instance.validate()

    def test_validate_validator_error(self) -> None:
        def validator(value: str) -> None:  # noqa: WPS430
            raise ValidatorError()

        class Container(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
                required=True,
                validator=validator,
            )

        instance = Container()
        instance.field = 'foo'
        with self.assertRaises(AttributesError):
            instance.validate()

    def test_export(self) -> None:
        class ChildAttributesContainer(AttributesContainer):  # noqa: WPS431
            field = Attribute.create(
                value_type=str,
            )

        class Container(AttributesContainer):  # noqa: WPS431
            str_field = Attribute.create(
                value_type=str,
            )
            int_field = Attribute.create(
                value_type=int,
            )
            bool_field = Attribute.create(
                value_type=bool,
            )
            sub_field = Attribute.create(
                value_type=ChildAttributesContainer,
            )

        child_instance = ChildAttributesContainer()
        child_instance.field = 'bar'

        instance = Container()
        instance.str_field = 'foo'
        instance.int_field = 123
        instance.bool_field = False
        instance.sub_field = child_instance
        exported = instance.export()
        self.assertEqual(
            dict(
                str_field='foo',
                int_field=123,
                bool_field=False,
                sub_field=dict(
                    field='bar',
                ),
            ),
            exported,
        )


class TestAttributesContainerList(unittest.TestCase):
    class ChildContainer(AttributesContainer):
        field = Attribute.create(
            value_type=str,
        )

    class Container(AttributesContainerList[ChildContainer]):
        def __init__(self) -> None:
            super().__init__(
                values_type=TestAttributesContainerList.ChildContainer,
                items=[],
            )

    def test_validate(self) -> None:
        child_instance = self.ChildContainer()
        child_instance.field = 'foo'
        instance = self.Container()
        instance.append(child_instance)
        instance.validate()

    def test_validate_invalid_child(self) -> None:
        child_instance = self.ChildContainer()
        child_instance.field = 123
        instance = self.Container()
        instance.append(child_instance)
        with self.assertRaises(AttributesError):
            instance.validate()

    def test_export(self) -> None:
        child_instance1 = self.ChildContainer()
        child_instance1.field = 'foo'
        child_instance2 = self.ChildContainer()
        child_instance2.field = 'bar'
        instance = self.Container()
        instance.append(child_instance1)
        instance.append(child_instance2)
        exported = instance.export()
        self.assertEqual(
            [
                dict(
                    field='foo',
                ),
                dict(
                    field='bar',
                ),
            ],
            exported,
        )


class TestAttributesContainerDict(unittest.TestCase):
    class ChildContainer(AttributesContainer):
        field = Attribute.create(
            value_type=str,
        )

    class Container(AttributesContainerDict[ChildContainer]):
        def __init__(self) -> None:
            super().__init__(
                values_type=TestAttributesContainerDict.ChildContainer,
                items={},
            )

    def test_validate(self) -> None:
        child1 = self.ChildContainer()
        child1.field = 'foo'
        child2 = self.ChildContainer()
        child2.field = 'bar'

        instance = self.Container()
        instance['child1'] = child1
        instance['child2'] = child2

        instance.validate()

    def test_validate_invalid_child(self) -> None:
        child_instance = self.ChildContainer()
        child_instance.field = 123
        instance = self.Container()
        instance['child'] = child_instance
        with self.assertRaises(AttributesError):
            instance.validate()

    def test_export(self) -> None:
        child1 = self.ChildContainer()
        child1.field = 'foo'
        child2 = self.ChildContainer()
        child2.field = 'bar'

        instance = self.Container()
        instance['child1'] = child1
        instance['child2'] = child2

        exported = instance.export()

        self.assertEqual(
            dict(
                child1=dict(
                    field='foo',
                ),
                child2=dict(
                    field='bar',
                ),
            ),
            exported,
        )
