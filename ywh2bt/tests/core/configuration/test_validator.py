from __future__ import annotations

import unittest
from typing import Optional, Type

from ywh2bt.core.configuration.validator import ValidatorError, url_validator


class TestValidator(unittest.TestCase):

    def when_validate(
        self,
        url: Optional[str],
    ) -> Assert:
        return Builder(
            test_case=self,
        ).with_url(
            url=url,
        ).when_validate()

    def test_valid_http(self) -> None:
        self.when_validate(
            url='http://example.com',
        ).then_assert_has_no_error()

    def test_valid_https(self) -> None:
        self.when_validate(
            url='https://example.com/test',
        ).then_assert_has_no_error()

    def test_valid_ftp(self) -> None:
        self.when_validate(
            url='ftp://example.com/test',
        ).then_assert_has_no_error()

    def test_valid_ftps(self) -> None:
        self.when_validate(
            url='ftps://example.com/test',
        ).then_assert_has_no_error()

    def test_valid_ip(self) -> None:
        self.when_validate(
            url='https://127.0.0.1/baz',
        ).then_assert_has_no_error()

    def test_valid_localhost(self) -> None:
        self.when_validate(
            url='https://localhost/bar',
        ).then_assert_has_no_error()

    def test_valid_port(self) -> None:
        self.when_validate(
            url='https://example.com:8080/foo',
        ).then_assert_has_no_error()

    def test_invalid_protocol(self) -> None:
        self.when_validate(
            url='ssh://example.com',
        ).then_assert_has_error_type(
            error_type=ValidatorError,
        )

    def test_invalid_none_url(self) -> None:
        self.when_validate(
            url=None,
        ).then_assert_has_error_type(
            error_type=TypeError,
        )

    def test_invalid_empty_url(self) -> None:
        self.when_validate(
            url='',
        ).then_assert_has_error_type(
            error_type=ValidatorError,
        )


class Builder:
    test_case: unittest.TestCase
    url: Optional[str]

    def __init__(
        self,
        test_case: unittest.TestCase,
    ):
        self.test_case = test_case

    def with_url(
        self,
        url: Optional[str],
    ) -> Builder:
        self.url = url
        return self

    def when_validate(self) -> Assert:
        error: Optional[Exception] = None
        if self.url is None:
            error = TypeError('Url should not be None')
        else:
            try:
                url_validator(self.url)
            except Exception as e:
                error = e
        return Assert(
            test_case=self.test_case,
            error=error,
        )


class Assert:
    test_case: unittest.TestCase
    error: Optional[Exception]

    def __init__(
        self,
        test_case: unittest.TestCase,
        error: Optional[Exception],
    ):
        self.test_case = test_case
        self.error = error

    def then_assert_has_no_error(self) -> Assert:
        self.test_case.assertIsNone(self.error)
        return self

    def then_assert_has_error_type(
        self,
        error_type: Type[Exception],
    ) -> Assert:
        self.test_case.assertIsInstance(self.error, error_type)
        return self
