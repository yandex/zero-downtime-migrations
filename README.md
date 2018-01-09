## UNDER DEVELOPMENT NOW

[![Build Status](https://travis-ci.org/Smosker/zero-downtime-migrations.svg?branch=master)](https://travis-ci.org/Smosker/zero-downtime-migrations)

## Description

Zero-Downtime-Migrations (ZDM) -- this is application which allow you to avoid long locks (and rewriting the whole table)
while applying Django migrations using PostgreSql as database.

## Installation
To install ZDM, simply run:
`$ pip install zero-downtime-migrations`

## Usage
If you are currently using default postresql backend change it to:
```
DATABASES = {
     'default': {
         'ENGINE': 'zero_downtime_migrations.backend',
         ...
     }
     ...
 }
```

If you are using your own custom backend you can:
- Set SchemaEditorClass if you are currently using default one
```
from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor

class YourCustomDatabaseWrapper(BaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
```
- Add ZeroDownTimeMixin to base classes of your DatabaseSchemaEditor
if you are using custom one
```
from zero_downtime_migrations.backend.schema import ZeroDownTimeMixin

class YourCustomSchemaEditor(ZeroDownTimeMixin, ...):
    ...
```

## Run tests

`./run_tests.sh`
