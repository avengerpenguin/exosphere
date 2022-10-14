#!/usr/bin/env python

from setuptools import setup

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
    extras_require={
        "test": [
            "pytest",
            "testypie",
            "httpretty",
            "pytest-pikachu",
            "pytest-mypy",
        ],
    },
    packages=["exosphere", "exosphere.stacks"],
    entry_points={
        "console_scripts": [
            "exosphere = exosphere.cli:main",
        ],
    },
)
