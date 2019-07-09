"""
Mixed-Content Crawler
"""
from setuptools import setup

setup(
    author='Matt Oberle',
    description='Mixed-Content Crawler',
    install_requires=[
        'beautifulsoup4',
        'chromedriver-binary==75.0.3770.8.0',
        'lxml',
        'requests',
        'selenium',
    ],
    long_description=__doc__,
    name='mixedcontent',
    packages=[
        'mixedcontent',
    ],
    scripts=[
        'scripts/mixedcontent',
    ],
    url='https://github.com/mattoberle/mixed-content',
    version='pre',
    zip_safe=True,
)
