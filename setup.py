# -*- coding: utf-8 -*-
#
# Redboy: Setup
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#

from setuptools import setup, find_packages
import os
import glob

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="Redboy",
      version='0.1.0',
      description="Object non-relational manager for Redis",
      url="http://github.com/SupermanScott/redboy/tree/master",
      packages=find_packages(),
      include_package_data=True,
      author="Scott Reynolds",
      author_email="Scott@scottreynolds.us",
      license="Three-clause BSD",
      keywords="database cassandra",
      install_requires=['redis'],
      zip_safe=False,
      tests_require=['nose', 'mock'],
      long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
        ])
