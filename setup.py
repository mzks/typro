#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os, re, ast
from setuptools import setup, find_packages


PACKAGE_NAME = 'typro'
with open(os.path.join(PACKAGE_NAME, '__init__.py')) as f:
    match = re.search(r'__version__\s+=\s+(.*)', f.read())
version = str(ast.literal_eval(match.group(1)))

try:
    with open('README.md') as f:
        readme = f.read()
except IOError:
    readme = ''

setup(
    name="typro",
    version="0.0.5",
    url='https://github.com/mzks/typro',
    author='Keita Mizukoshi',
    author_email='mzks@stu.kobe-u.ac.jp',
    maintainer='Keita Mizukoshi',
    maintainer_email='mzks@stu.kobe-u.ac.jp',
    description='typing game on console',
    long_description=readme,
    packages=find_packages(),
    install_requires=['numpy', 'pandas'],
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
    'console_scripts': [ 'typro=typro.cli:main' ]
    }
)
