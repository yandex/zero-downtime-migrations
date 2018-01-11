## UNDER DEVELOPMENT NOW

[![Build Status](https://travis-ci.org/Smosker/zero-downtime-migrations.svg?branch=master)](https://travis-ci.org/Smosker/zero-downtime-migrations)

## Description

Zero-Downtime-Migrations (ZDM) -- this is application which allow you to avoid long locks (and rewriting the whole table)
while applying Django migrations using PostgreSql as database.

## Current possibilities
- add field with default value (nullable or not)

## Why use it

We face such a problem - performing some django migrations (such as add column with default value) lock the table on
read/write, so its impossible for our services to work properly during this periods. It can be acceptable on rather small
tables (less than million rows), but even on them it can be painfull if services is high loaded.
But we have a lot of tables with more than 50 millions rows, and applying migrations on such table lock it for
more than an hour, which is totally unacceptable. Also during this time consuming operations migration rather often fail
because of different errors (such as TimeoutError) and we have to start it from scratch or run sql manually thought
psql and when fake migration.

So in the end we have an idea of writing this package so it can prevent long locks on table and also
provide more stable migration process which can be continue if operation fall for some reason.

## Example

When adding not null column with default django will perform such sql query:

`ALTER TABLE "test" ADD COLUMN "field" boolean DEFAULT True NOT NULL`

Which cause postgres to rewrite the whole table and when swap it with existing one
https://docs.djangoproject.com/en/2.0/topics/migrations/#postgresql and during this period
it will hold exclusive lock on write/read on this table.

This package will break sql above in separate commands not only to prevent the rewriting of whole
table but also to add column with as small lock times as possible.

First of all we will add nullable column without default and add default value to it in one transaction:

`ALTER TABLE "test" ADD COLUMN "field" boolean NULL;`

`ALTER TABLE "test" ALTER COLUMN "field" SET DEFAULT true;`

This will add default for all new rows in table but all existing ones will be with null value in this column for now,
this operation will be quick because postgres doesn't have to fill all existing rows with default.

Next we will count objects in table and if result if more than zero - calculate the
size of batch in witch we will update existing rows. After that while where are still objects with null in this
column - we will update them.

While result of following statement is more than zero:
```WITH cte AS (
SELECT <table_pk_column> as pk
FROM "test"
WHERE  "field" is null
LIMIT  <size_calculated_on_previous_step>
)
UPDATE "test" table_
SET "field" = true
FROM   cte
WHERE  table_.<table_pk_column> = cte.pk
```

When we have no more rows with null in this column we can set not null and drop default (this is django default
 behavior):

`ALTER TABLE "test" ALTER COLUMN "field" SET NOT NULL;`

`ALTER TABLE "test" ALTER COLUMN "field" DROP DEFAULT;`

So we finish add field process.
It will be definitely more time consuming than basic variant with one sql statement, but in this approach
there are no long locks on table so service can work normally during this migrations process.


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
- Set `SchemaEditorClass` if you are currently using default one:
```
from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor

class YourCustomDatabaseWrapper(BaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
```
- Add `ZeroDownTimeMixin` to base classes of your `DatabaseSchemaEditor`
if you are using custom one:
```
from zero_downtime_migrations.backend.schema import ZeroDownTimeMixin

class YourCustomSchemaEditor(ZeroDownTimeMixin, ...):
    ...
```

## Run tests

`./run_tests.sh`
