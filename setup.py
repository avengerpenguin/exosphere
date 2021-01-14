#!/usr/bin/env python

from setuptools import setup
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    user_options = [("tox-args=", "a", "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import shlex

        import tox

        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


setup(
    name="exosphere",
    use_scm_version={
        "local_scheme": "dirty-tag",
        "write_to": "exosphere/_version.py",
        "fallback_version": "0.0.0",
    },
    author="Ross Fenning",
    author_email="github@rossfenning.co.uk",
    description="Pre-built, useful Cloudformation stacks and commands to work with them.",
    url="http://github.com/TheLaunchNinja/exosphere",
    install_requires=["troposphere", "boto3", "clize", "awacs"],
    setup_requires=["setuptools_scm>=3.3.1"],
    packages=["exosphere", "exosphere.stacks"],
    entry_points={
        "console_scripts": [
            "exosphere = exosphere.cli:main",
        ],
    },
)
