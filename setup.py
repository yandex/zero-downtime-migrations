from setuptools import setup, find_packages

setup(
    name='zero-downtime-migrations',
    version='0.1',
    author='Vladimir Koljasinskij',
    author_email='smosker@gmail.com',
    url='https://github.com/Smosker/zero-downtime-migrations',
    description='django migrations without long locks',
    packages=find_packages(),
    install_requires=[
        'Django>=1.3',
        'psycopg2>=2.7.3.2',
    ]
)
