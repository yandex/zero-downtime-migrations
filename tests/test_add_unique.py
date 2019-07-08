# coding: utf-8

from __future__ import unicode_literals

import pytest
import django
import re

from distutils.version import StrictVersion
from django.db import models
from django.db import connections
from django.test.utils import CaptureQueriesContext

from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor
from test_app.models import TestModel

connection = connections['default']
schema_editor = DatabaseSchemaEditor
DJANGO_VERISON = StrictVersion(django.get_version())


@pytest.mark.django_db(transaction=True)
def test_add_unique_correct_queries():
    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(unique=True)
    field.set_attributes_from_name("name")
    if DJANGO_VERISON >= StrictVersion('2.1'):
        index_pattern = r'CREATE UNIQUE INDEX CONCURRENTLY "test_app_testmodel_name_\w+(_uniq)?" ON "test_app_testmodel" \("name"\)'
        check_index_pattern = r"SELECT 1 FROM pg_class, pg_index WHERE pg_index.indisvalid = false AND pg_index.indexrelid = pg_class.oid and pg_class.relname = 'test_app_testmodel_name_\w+(_uniq)?'"
        constraint_pattern = r'ALTER TABLE test_app_testmodel ADD CONSTRAINT test_app_testmodel_name_\w+(_uniq)? UNIQUE USING INDEX test_app_testmodel_name_\w+(_uniq)?'
        expected_queries = 3
    else:
        index_pattern = r'ALTER TABLE "test_app_testmodel" ADD CONSTRAINT "?test_app_testmodel_name_\w+(_uniq)?"? UNIQUE \("name"\)'
        check_index_pattern = None
        constraint_pattern = None
        expected_queries = 1
    with CaptureQueriesContext(connection) as ctx, schema_editor(connection=connection) as editor:
        editor.alter_field(TestModel, old_field, field)
        assert len(ctx.captured_queries) == expected_queries
        assert re.search(index_pattern, ctx.captured_queries[0]['sql']) is not None
        if check_index_pattern:
            assert re.search(check_index_pattern, ctx.captured_queries[1]['sql']) is not None
        if constraint_pattern:
            assert re.search(constraint_pattern, ctx.captured_queries[2]['sql']) is not None


@pytest.mark.django_db(transaction=True)
def test_add_unique_correct_result():
    old_field = models.IntegerField()
    old_field.set_attributes_from_name("name")

    field = models.IntegerField(unique=True)
    field.set_attributes_from_name("name")
    with schema_editor(connection=connection) as editor:
        editor.alter_field(TestModel, old_field, field)
    TestModel.objects.create(name='test')
    TestModel.objects.create(name='smth')
    with pytest.raises(django.db.utils.IntegrityError):
        TestModel.objects.create(name='test')
