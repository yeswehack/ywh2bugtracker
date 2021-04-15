import marshmallow
from aiosnow.query import StringQueryable as StringQueryable

from .base import BaseField as BaseField


class String(marshmallow.fields.String, BaseField, StringQueryable): ...
