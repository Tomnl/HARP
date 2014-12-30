from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'Interpolator',
  ext_modules = cythonize("interpolator.pyx"),
)
