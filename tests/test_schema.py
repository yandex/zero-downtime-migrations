# coding: utf-8

from __future__ import unicode_literals

import pytest

from django.db import models
from django.db import connections

from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor
from .test_app.models import TestModel

pytestmark = pytest.mark.django_db
connection = connections['default']
schema_editor = DatabaseSchemaEditor


@pytest.mark.skip(reason='Not working now')
def test_retry_working():
    sql = 'ALTER TABLE "test_app_testmodel" ADD COLUMN "bool_field" boolean NULL;'
    with connection.cursor() as cursor:
        cursor.execute(sql, ())

    field = models.BooleanField(default=True)
    field.set_attributes_from_name("bool_field")
    with schema_editor(connection=connection) as editor:
        editor.add_field(TestModel, field)
