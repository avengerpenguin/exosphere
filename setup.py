#!/usr/bin/env python

import os
from setuptools import setup
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


setup(
    name="exosphere",
    version="0.0.0",
    author='The Launch Ninja',
    author_email='exosphere@thelaunch.ninja',
    description='Pre-built, useful Cloudformation stacks and commands to work with them.',
    url='http://github.com/bbc/exosphere',
    install_requires=['troposphere', 'boto3', 'clize'],
    packages=['exosphere', 'exosphere.stacks'],
    entry_points={
        'console_scripts': [
            'exosphere = exosphere.cli:main',
        ],
    },
    tests_require=['pytest', 'pytest-cov', 'tox', 'virtualenv', 'httpretty'],
    cmdclass = {'test': Tox},
)
