import marshmallow
from aiosnow.query import BooleanQueryable as BooleanQueryable

from .base import BaseField as BaseField


class Boolean(marshmallow.fields.Boolean, BaseField, BooleanQueryable): ...
