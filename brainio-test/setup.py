#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='brainio-test',
    version='0.1.0',
    description="Lookup data for testing BrainIO",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'brainio_lookups': [
            'brainio_test = brainio_test.entrypoint:brainio_test',
        ],
    },
)
