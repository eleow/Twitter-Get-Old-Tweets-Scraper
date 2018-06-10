#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    "pyquery>=1.2.17",
    "requests>=2.13.0",
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Felipe Arruda",
    author_email='contato@arruda.blog.br',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    install_requires=requirements,
    include_package_data=True,
    name='old_tweets_crawler',
    packages=find_packages(include=['old_tweets_crawler']),
    url='https://github.com/arruda/Twitter-Get-Old-Tweets-Scraper',
    version='0.1.0',
    zip_safe=False,
)
