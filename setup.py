#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 by science+computing ag
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#


from setuptools import setup
import sys
from conf import release

setup(
    name='quickimport',
    version=release,
    description='Fast imports for rapid application startup',
    author='Anselm Kruis',
    author_email='a.kruis@science-computing.de',
    url='http://pypi.python.org/pypi/quickimport',
    py_modules=['quickimport'],
    zip_safe = True,

    # don't forget to add these files to MANIFEST.in too

    long_description=
"""
Quickimport - Fast import of modules
------------------------------------

The module quickimport provides an improved importer for python. If 
you ever started a Python application from a lame file server (like 
a CIFS server) you know the problem of long startup times. The quickimport
importer uses the pep 302 import hooks to reduce the number of 
failing stat system calls for each loaded module.

For Python 2.7. May work with earlier versions too.

Git repository: git://github.com/akruis/quickimport.git
""",
    classifiers=[
          "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Environment :: Other Environment",
          "Operating System :: OS Independent",
          "Development Status :: 3 - Alpha", # hasn't been tested outside of flowGuide2
          "Intended Audience :: Developers",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='import pep302 performance zipimport',
      license='GNU Lesser General Public License, version 2.1 or any later version',
      platforms="any",
      test_suite="testQuickimport"
    
    )
