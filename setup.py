#!/usr/bin/env python

try:
    from setuptools import setup
    setup
except ImportError:
    from distutils.core import setup

import opslib

setup(name='opslib',
      version=opslib.__version__,
      sescription='Library for AWS Operations',
      packages=["opslib", "opslib.icsutils"],
      package_data={"opslib": ["opslib.ini"]},
      author="Henry Huang",
      author_email="henry.s.huang@gmail.com",
      url="https://github.com/henrysher/opslib",
      license='Apache 2.0',
      include_package_data=True,
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Natural Language :: English',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Installation/Setup',
          'Topic :: Utilities',
      ],
      install_requires=[
          'setuptools',
          'boto',
          'botocore',
          'argcomplete',
      ],
      )
