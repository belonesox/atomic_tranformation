#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = [
    'pytz',
    'trans'
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Stas Fomin",
    author_email='stas-fomin@yandex.ru',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Atomic action on files",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords='atomic_transformation',
    name='atomic_transformation',
    packages=find_packages(include=['atomic_transformation', 'atomic_transformation.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/belonesox/atomic_transformation',
    version='0.1.0',
    zip_safe=False,
)
