#!/usr/bin/env python

from setuptools import setup

setup(name='opslib',
      version='1.0',
      description='Library for ICS Operations',
      packages=['opslib', 'opslib.icsutils'],
      package_data = {"opslib": ["conf/opslib.ini"]},
      license='Apache 2.0',
      install_requires=[
        'setuptools',
        'boto',
      ],
     )
