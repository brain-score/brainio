#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    "six",
    "boto3",
    "tqdm",
    "Pillow",
    "entrypoints",
    "numpy",
    "pandas",
    "xarray!=2022.6.0,!=2022.9.0",  # 2022.{6,9} have a groupby bug: https://github.com/pydata/xarray/issues/6836
    "netcdf4!=1.6.0",  # https://github.com/Unidata/netcdf4-python/issues/1175,
]

setup(
    name='brainio',
    version='0.2.0',
    description="Data management for quantitative comparison of brains and brain-inspired systems",
    long_description=readme,
    author="Jon Prescott-Roy, Martin Schrimpf",
    author_email='jjpr@mit.edu, mschrimpf@mit.edu',
    url='https://github.com/brain-score/brainio',
    packages=find_packages(exclude=['tests', 'brainio-test']),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "tests": [
            "pytest",
            "imageio",
        ],
    },
    license="MIT license",
    zip_safe=False,
    keywords='BrainIO',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
)
