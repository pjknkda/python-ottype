import os
import re
import sys
from os import path

from setuptools import Extension, setup

wdir = path.abspath(path.dirname(__file__))

with open(path.join(wdir, 'ottype', '__init__.py'), encoding='utf-8') as f:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$", f.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

with open(path.join(wdir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


NO_EXTENSIONS = bool(os.environ.get('OTTYPE_NO_EXTENSIONS'))
if sys.implementation.name != 'cpython':
    NO_EXTENSIONS = True

try:
    from Cython.Build import cythonize
except ImportError:
    NO_EXTENSIONS = True

dev_install_requires = [
    'autopep8==1.6.0',
    'bandit==1.7.4',
    'Cython==0.29.28',
    'flake8==4.0.1',
    'flake8-bugbear==22.1.11',
    'flake8-isort==4.1.1',
    'flake8-quotes==3.3.1',
    'mypy==0.931',
    'pytest==7.0.1',
    'pytest-cov==3.0.0',
]

if not NO_EXTENSIONS:
    ext_modules = cythonize([
        Extension('ottype.core_boost', ['ottype/core_boost.pyx'])
    ])
else:
    ext_modules = []

setup(
    name='python-ottype',
    version=version,
    description='A python implementation of Operational Transformation.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='ottype',

    author='Jungkook Park',
    author_email='pjknkda@gmail.com',
    url='https://github.com/pjknkda/python-ottype',
    license='MIT',

    packages=['ottype'],
    package_data={'ottype': ['py.typed']},
    zip_safe=False,

    python_requires='>=3.7, <3.11',

    extras_require={'dev': dev_install_requires},

    ext_modules=ext_modules,

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
