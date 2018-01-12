# coding: utf-8

from __future__ import unicode_literals

import pytest
import re

from django.db import models
from django.db import connections
from django.test.utils import CaptureQueriesContext

from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor
from test_app.models import TestModel

connection = connections['default']
schema_editor = DatabaseSchemaEditor


@pytest.mark.django_db(transaction=True)
def test_create_index_success():
    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(db_index=True)
    field.set_attributes_from_name("name")
    pattern = r'CREATE INDEX CONCURRENTLY "test_app_testmodel_name_\w+(_uniq)?" ON "test_app_testmodel" \("name"\)'
    with CaptureQueriesContext(connection) as ctx, schema_editor(connection=connection) as editor:
        editor.alter_field(TestModel, old_field, field)
        assert len(ctx.captured_queries) == 1
        assert re.search(pattern, ctx.captured_queries[0]['sql']) is not None


def test_sqlmigrate_create_index_working():
    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(db_index=True)
    field.set_attributes_from_name("name")
    pattern = r'CREATE INDEX CONCURRENTLY "test_app_testmodel_name_\w+(_uniq)?" ON "test_app_testmodel" \("name"\)'
    with schema_editor(connection=connection, collect_sql=True) as editor:
        editor.alter_field(TestModel, old_field, field)
        assert len(editor.collected_sql) == 1
        assert re.search(pattern, editor.collected_sql[0]) is not None
