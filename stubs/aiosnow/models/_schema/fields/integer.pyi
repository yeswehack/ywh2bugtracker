import marshmallow
from aiosnow.query import IntegerQueryable as IntegerQueryable

from .base import BaseField as BaseField


class Integer(marshmallow.fields.Integer, BaseField, IntegerQueryable): ...
