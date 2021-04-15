import marshmallow
from aiosnow.query import DateTimeQueryable as DateTimeQueryable

from .base import BaseField as BaseField


class DateTime(marshmallow.fields.DateTime, BaseField, DateTimeQueryable): ...
