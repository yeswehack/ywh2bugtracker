import unittest


def run() -> None:
    loader = unittest.TestLoader()
    tests = loader.discover('.')
    test_runner = unittest.runner.TextTestRunner(verbosity=2)
    test_runner.run(tests)


if __name__ == '__main__':
    run()
