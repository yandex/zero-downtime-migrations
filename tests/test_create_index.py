# coding: utf-8

from __future__ import unicode_literals

import pytest
import re
import django

from django.db import models
from django.db import connections
from django.test.utils import CaptureQueriesContext
from distutils.version import StrictVersion

from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor
from zero_downtime_migrations.backend.exceptions import InvalidIndexError
from test_app.models import TestModel

connection = connections['default']
schema_editor = DatabaseSchemaEditor
DJANGO_VERISON = StrictVersion(django.get_version())


@pytest.mark.django_db(transaction=True)
def test_create_index_success():
    TestModel.objects.all().delete()
    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(db_index=True)
    field.set_attributes_from_name("name")
    pattern = r'CREATE INDEX CONCURRENTLY "test_app_testmodel_name_\w+(_uniq)?" ON "test_app_testmodel" \("name"\)'
    search_pattern = r"SELECT 1 FROM pg_class, pg_index WHERE pg_index.indisvalid = false AND pg_index.indexrelid = pg_class.oid and pg_class.relname = 'test_app_testmodel_name_\w+(_uniq)?'"
    with CaptureQueriesContext(connection) as ctx, schema_editor(connection=connection) as editor:
        editor.alter_field(TestModel, old_field, field)
        assert len(ctx.captured_queries) == 2
        assert re.search(pattern, ctx.captured_queries[0]['sql']) is not None
        assert re.search(search_pattern, ctx.captured_queries[1]['sql']) is not None


@pytest.mark.django_db(transaction=True)
def test_sqlmigrate_create_index_working():
    TestModel.objects.all().delete()
    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(db_index=True)
    field.set_attributes_from_name("name")
    pattern = r'CREATE INDEX CONCURRENTLY "test_app_testmodel_name_\w+(_uniq)?" ON "test_app_testmodel" \("name"\)'
    with schema_editor(connection=connection, collect_sql=True) as editor:
        editor.alter_field(TestModel, old_field, field)
        assert len(editor.collected_sql) == 1
        assert re.search(pattern, editor.collected_sql[0]) is not None


@pytest.mark.django_db(transaction=True)
def test_create_index_fail():
    TestModel.objects.create(name='test_unique')
    TestModel.objects.create(name='test_unique')

    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(unique=True)
    field.set_attributes_from_name("name")

    if DJANGO_VERISON >= StrictVersion('2.1'):
        create_pattern = r'CREATE UNIQUE INDEX CONCURRENTLY "test_app_testmodel_name_\w+(_uniq)?" ON "test_app_testmodel" \("name"\)'
        search_pattern = r"SELECT 1 FROM pg_class, pg_index WHERE pg_index.indisvalid = false AND pg_index.indexrelid = pg_class.oid and pg_class.relname = 'test_app_testmodel_name_\w+(_uniq)?'"
        drop_pattern = r"DROP INDEX CONCURRENTLY IF EXISTS test_app_testmodel_name_\w+(_uniq)?"
        with CaptureQueriesContext(connection) as ctx, schema_editor(connection=connection) as editor:
            with pytest.raises(InvalidIndexError):
                editor.alter_field(TestModel, old_field, field)
            assert len(ctx.captured_queries) == 3
            assert re.search(create_pattern, ctx.captured_queries[0]['sql']) is not None
            assert re.search(search_pattern, ctx.captured_queries[1]['sql']) is not None
            assert re.search(drop_pattern, ctx.captured_queries[2]['sql']) is not None
    else:
        with CaptureQueriesContext(connection) as ctx, schema_editor(connection=connection) as editor:
            index_pattern = r'ALTER TABLE "test_app_testmodel" ADD CONSTRAINT "?test_app_testmodel_name_\w+(_uniq)?"? UNIQUE \("name"\)'
            with pytest.raises(django.db.utils.IntegrityError):
                editor.alter_field(TestModel, old_field, field)
            assert len(ctx.captured_queries) == 1
            assert re.search(index_pattern, ctx.captured_queries[0]['sql']) is not None
