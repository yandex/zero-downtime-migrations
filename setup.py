# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='zero-downtime-migrations',
    version='0.10',
    author='Vladimir Koljasinskij',
    author_email='smosker@yandex-team.ru',
    license='BSD-3-Clause',
    url='https://github.com/yandex/zero-downtime-migrations',
    description='django migrations without long locks',
    long_description=read('README.rst'),
    classifiers=['Development Status :: 4 - Beta',
                 'Framework :: Django',
                 'Framework :: Django :: 1.8',
                 'Framework :: Django :: 1.9',
                 'Framework :: Django :: 1.10',
                 'Framework :: Django :: 1.11',
                 'Framework :: Django :: 2.0',
                 'Framework :: Django :: 2.1',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 ],
    keywords='django postgresql migrations',
    packages=find_packages(),
    python_requires='>=2.7,!=3.1.*,!=3.0.*,!=3.2.*,!=3.3.*,<4.0',
    install_requires=[
        'Django>=1.3',
        'psycopg2>=2.7.3.2',
    ]
)
