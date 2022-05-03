#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

from pyzerproc import __author__, __email__, __version__

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'Click>=7.0',
    'bleak>=0.11.0',
]

test_requirements = ['pytest>=6.2.2', ]

setup(
    author=__author__,
    author_email=__email__,
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    description=(
        "Async library to control Zerproc Bluetooth LED smart string lights"),
    entry_points={
        'console_scripts': [
            'pyzerproc=pyzerproc.cli:main',
        ],
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    include_package_data=True,
    keywords='pyzerproc',
    name='pyzerproc',
    packages=find_packages(include=['pyzerproc', 'pyzerproc.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/emlove/pyzerproc',
    version=__version__,
    zip_safe=False,
)
