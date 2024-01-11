import sys
import unittest


def run() -> None:
    loader = unittest.TestLoader()
    tests = loader.discover(".", pattern="test_*.py")
    test_runner = unittest.runner.TextTestRunner(verbosity=2)
    print(f"Running tests with python {sys.version}", file=sys.stderr)
    result = test_runner.run(tests)
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    run()
