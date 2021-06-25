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
    "numpy>=1.16.5, !=1.21.0",
    "pandas>=1.2.0",
    "xarray>=0.17.0", # a bug introduced in 0.16.2 causes align to handle MultiIndex wrong
    # test_requirements
    "pytest",
    "imageio",
    "entrypoints",
]

setup(
    name='brainio',
    version='0.1.0',
    description="Data management for quantitative comparison of brains and brain-inspired systems",
    long_description=readme,
    author="Jon Prescott-Roy, Martin Schrimpf",
    author_email='jjpr@mit.edu, mschrimpf@mit.edu',
    url='https://github.com/brain-score/brainio',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=requirements,
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
    entry_points={
        'brainio_lookups': [
            'brainio_test = brainio.entrypoint:brainio_test',
        ],
    },
)
