import os
import unittest

from ywh2bt.cli.main import run as cli_run
from ywh2bt.tests.std_redirect import StdRedirect
from ywh2bt.version import __VERSION__


def _resource(
    path: str,
) -> str:
    return os.path.join(os.path.dirname(__file__), 'resources', path)


class TestCli(unittest.TestCase):
    def _test_version(
        self,
        flag: str,
    ) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                flag,
            )
        self.assertEqual(0, se.exception.code)
        self.assertIn(__VERSION__, outputs.get_stdout())
        self.assertEqual('', outputs.get_stderr())

    def test_version_long(self) -> None:
        self._test_version(
            flag='--version',
        )

    def test_version_short(self) -> None:
        self._test_version(
            flag='-V',
        )

    def test_file_not_found(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/does-not-exist.json")}',
            )
        self.assertEqual(1, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertNotEqual('', outputs.get_stderr())

    def test_invalid_format(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/valid.json")}',
                '--config-format=foo',
            )
        self.assertEqual(2, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertNotEqual('', outputs.get_stderr())

    def test_valid_json(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/valid.json")}',
                '--config-format=json',
            )
        self.assertEqual(0, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertEqual('', outputs.get_stderr())

    def test_invalid_json(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/invalid.json")}',
                '--config-format=json',
            )
        self.assertEqual(1, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertIn('Invalid configuration', outputs.get_stderr())

    def test_valid_yaml(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/valid.yml")}',
                '--config-format=yaml',
            )
        self.assertEqual(0, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertEqual('', outputs.get_stderr())

    def test_invalid_yaml(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/invalid.yml")}',
                '--config-format=yaml',
            )
        self.assertEqual(1, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertNotEqual('', outputs.get_stderr())

    def test_format_mismatch(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/invalid.yml")}',
                '--config-format=json',
            )
        self.assertEqual(1, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertNotEqual('', outputs.get_stderr())

    def test_not_root(self) -> None:
        with self.assertRaises(SystemExit) as se, StdRedirect.redirect() as outputs:
            cli_run(
                'validate',
                f'--config-file={_resource("configurations/not-root.json")}',
                '--config-format=json',
            )
        self.assertEqual(1, se.exception.code)
        self.assertEqual('', outputs.get_stdout())
        self.assertNotEqual('', outputs.get_stderr())
