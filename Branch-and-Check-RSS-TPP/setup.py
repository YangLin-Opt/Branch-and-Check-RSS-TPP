# -*- coding: UTF-8 -*-

from distutils.core import setup, Extension
from Cython.Build import cythonize

setup(ext_modules=cythonize("ctools.pyx", language_level=3))
