#!/usr/bin/env python

import os
from setuptools import setup

setup(
    name="exosphere",
    version="0.0.0",
    author='The Launch Ninja',
    author_email='ross@thelaunch.ninja',
    description='Pre-built, useful Cloudformation stacks and commands to work with them.',
    url='http://github.com/bbc/exosphere',
    install_requires=['troposphere', 'boto3', 'clize'],
    packages=['exosphere'],
    entry_points={
        'console_scripts': [
            'exosphere = cumulus.cli:main',
        ],
    },
)
