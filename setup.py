# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='zero-downtime-migrations',
    version='0.1',
    author='Vladimir Koljasinskij',
    author_email='smosker@gmail.com',
    license='BSD-3-Clause',
    url='https://github.com/Smosker/zero-downtime-migrations',
    description='django migrations without long locks',
    classifiers=['Development Status :: 3 - Alpha',
                 'Framework :: Django',
                 'Framework :: Django :: 1.8',
                 'Framework :: Django :: 1.9',
                 'Framework :: Django :: 1.10',
                 'Framework :: Django :: 1.11',
                 'Framework :: Django :: 2.0',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.5',
                 ],
    packages=find_packages(),
    install_requires=[
        'Django>=1.3',
        'psycopg2>=2.7.3.2',
    ]
)
