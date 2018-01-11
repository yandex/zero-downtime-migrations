# coding: utf-8

from __future__ import unicode_literals

import pytest

from django.db import models
from django.db import connections

from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor
from test_app.models import TestModel

pytestmark = pytest.mark.django_db
connection = connections['default']
schema_editor = DatabaseSchemaEditor


def test_sqlmigrate_working():
    field = models.BooleanField(default=True)
    field.set_attributes_from_name("bool_field")
    with schema_editor(connection=connection, collect_sql=True) as editor:
        editor.add_field(TestModel, field)
        assert editor.collected_sql == [
            "SELECT IS_NULLABLE, DATA_TYPE, COLUMN_DEFAULT from information_schema.columns where table_name = 'test_app_testmodel' and column_name = 'bool_field';",
            'ALTER TABLE "test_app_testmodel" ADD COLUMN "bool_field" boolean NULL;',
            'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" SET DEFAULT true;',
            "SELECT reltuples::BIGINT FROM pg_class WHERE relname = 'test_app_testmodel';",
            '\n                       WITH cte AS (\n                       SELECT id as pk\n                       FROM test_app_testmodel\n                       WHERE  bool_field is null\n                       LIMIT  1000\n                       )\n                       UPDATE test_app_testmodel table_\n                       SET bool_field = true\n                       FROM   cte\n                       WHERE  table_.id = cte.pk\n                       ;',
            'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" SET NOT NULL;',
            'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" DROP DEFAULT;'
        ]


@pytest.mark.skip(reason='Not working now')
def test_retry_working():
    sql = 'ALTER TABLE "test_app_testmodel" ADD COLUMN "bool_field" boolean NULL;'
    with connection.cursor() as cursor:
        cursor.execute(sql, ())

    field = models.BooleanField(default=True)
    field.set_attributes_from_name("bool_field")
    with schema_editor(connection=connection) as editor:
        editor.add_field(TestModel, field)
