# coding: utf-8

from __future__ import unicode_literals

import pytest
from mock import patch, call

from django.db import models
from django.db import connections
from django.db.migrations.questioner import InteractiveMigrationQuestioner
from django.test.utils import CaptureQueriesContext

from zero_downtime_migrations.backend.schema import DatabaseSchemaEditor
from test_app.models import TestModel

pytestmark = pytest.mark.django_db
connection = connections['default']
schema_editor = DatabaseSchemaEditor


@pytest.fixture
def add_column():
    sql = 'ALTER TABLE "test_app_testmodel" ADD COLUMN "bool_field" BOOLEAN NULL;'
    with connection.cursor() as cursor:
        cursor.execute(sql, ())


def base_questioner_test(choice_return):
    field = models.BooleanField(default=True)
    field.set_attributes_from_name("bool_field")
    with CaptureQueriesContext(connection) as ctx:
        with patch.object(InteractiveMigrationQuestioner, '_choice_input') as choice_mock:
            with schema_editor(connection=connection) as editor:
                choice_mock.return_value = choice_return
                editor.add_field(TestModel, field)

                queries = [query_data['sql'] for query_data in ctx.captured_queries
                           if 'test_app' in query_data['sql']]
    return choice_mock, queries


def test_retry_with_exit_working(add_column):
    with pytest.raises(SystemExit):
        base_questioner_test(1)


def test_retry_with_drop_working(add_column):
    _, queries = base_questioner_test(2)
    assert queries == [("SELECT IS_NULLABLE, DATA_TYPE, COLUMN_DEFAULT from information_schema.columns "
                        "where table_name = 'test_app_testmodel' and column_name = 'bool_field';"),
                       'ALTER TABLE "test_app_testmodel" DROP COLUMN "bool_field" CASCADE',
                       'ALTER TABLE "test_app_testmodel" ADD COLUMN "bool_field" boolean NULL',
                       'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" SET DEFAULT true',
                       "SELECT reltuples::BIGINT FROM pg_class WHERE relname = 'test_app_testmodel';",
                       'SELECT COUNT(*) FROM test_app_testmodel;',
                       'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" SET NOT NULL',
                       'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" DROP DEFAULT',
                       ]


def test_retry_with_choice_working(add_column):
    choice_mock, queries = base_questioner_test(3)
    calls = [call(('It look like column "bool_field" in table '
                   '"test_app_testmodel" already exist with '
                   'following parameters: TYPE: "boolean", '
                   'DEFAULT: "None", NULLABLE: "YES".'),
                  ('abort migration', u'drop column and run migration from beginning',
                   'manually choose action to start from',
                   'show how many rows still need to be updated',
                   'mark operation as successful and proceed to next operation',
                   'drop column and run migration from standard SchemaEditor',
                   ),
                  ),
             call('Now choose from which action process should continue',
                  ['add field with default',
                   'update existing rows',
                   'set not null for field',
                   'drop default',
                   ]),
             ]
    choice_mock.assert_has_calls(calls)
    assert queries == [("SELECT IS_NULLABLE, DATA_TYPE, COLUMN_DEFAULT from information_schema.columns where "
                        "table_name = 'test_app_testmodel' and column_name = 'bool_field';"),
                       'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" SET NOT NULL',
                       'ALTER TABLE "test_app_testmodel" ALTER COLUMN "bool_field" DROP DEFAULT',
                       ]


def test_retry_with_skip_working(add_column):
    choice_mock, queries = base_questioner_test(5)
    choice_mock.assert_called_once_with(('It look like column "bool_field" in table '
                                         '"test_app_testmodel" already exist with '
                                         'following parameters: TYPE: "boolean", '
                                         'DEFAULT: "None", NULLABLE: "YES".'),
                                        ('abort migration', u'drop column and run migration from beginning',
                                         'manually choose action to start from',
                                         'show how many rows still need to be updated',
                                         'mark operation as successful and proceed to next operation',
                                         'drop column and run migration from standard SchemaEditor',
                                         ),
                                        )
    assert len(queries) == 1
    assert queries[0] == ("SELECT IS_NULLABLE, DATA_TYPE, COLUMN_DEFAULT from information_schema.columns "
                          "where table_name = 'test_app_testmodel' and column_name = 'bool_field';")
