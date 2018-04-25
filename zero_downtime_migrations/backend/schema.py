# coding: utf-8

from __future__ import unicode_literals

import sys
import inspect

from distutils.version import StrictVersion

try:
    from django.db.backends.postgresql.schema import DatabaseSchemaEditor as BaseEditor
except ImportError:
    from django.db.backends.postgresql_psycopg2.schema import DatabaseSchemaEditor as BaseEditor

import django
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.related import RelatedField
from django.db import transaction
from django.db.migrations.questioner import InteractiveMigrationQuestioner

DJANGO_VERISON = StrictVersion(django.get_version())


class ZeroDownTimeMixin(object):
    sql_estimate_count_in_table = "SELECT reltuples::BIGINT FROM pg_class WHERE relname = '%(table)s';"
    sql_count_in_table = "SELECT COUNT(*) FROM %(table)s;"
    sql_count_in_table_with_null = "SELECT COUNT(*) FROM %(table)s WHERE %(column)s is NULL;"
    sql_update_batch = '''
                       WITH cte AS (
                       SELECT %(pk_column_name)s as pk
                       FROM %(table)s
                       WHERE  %(column)s is null
                       LIMIT  %(batch_size)s
                       )
                       UPDATE %(table)s table_
                       SET %(column)s = %(value)s
                       FROM   cte
                       WHERE  table_.%(pk_column_name)s = cte.pk
                       '''
    sql_check_column_status = ("SELECT IS_NULLABLE, DATA_TYPE, COLUMN_DEFAULT from information_schema.columns "
                               "where table_name = '%(table)s' and column_name = '%(column)s';")

    def add_field(self, model, field):
        if isinstance(field, RelatedField) or field.default is NOT_PROVIDED:
            return super(ZeroDownTimeMixin, self).add_field(model, field)
        else:
            # Checking which actions we should perform - maybe this operation was run
            # before and it had crashed for some reason
            actions = self.get_actions_to_perform(model, field)
            if len(actions) == 0:
                return

            # Saving initial values
            default_effective_value = self.effective_default(field)
            nullable = field.null
            # Update the values to the required ones
            field.default = None if DJANGO_VERISON < StrictVersion('1.11') else NOT_PROVIDED
            if nullable is False:
                field.null = True

            # For Django < 1.10
            atomic = getattr(self, 'atomic_migration', True)

            if self.connection.in_atomic_block:
                self.atomic.__exit__(None, None, None)

            available_args = {
                'model': model,
                'field': field,
                'nullable': nullable,
                'default_effective_value': default_effective_value,
            }
            # Performing needed actions
            for action in actions:
                action = '_'.join(action.split())
                func = getattr(self, action)
                func_args = {arg: available_args[arg] for arg in
                             inspect.getargspec(func).args if arg != 'self'
                             }
                func(**func_args)

            # If migrations was atomic=True initially
            # entering atomic block again
            if atomic:
                self.atomic = transaction.atomic(self.connection.alias)
                self.atomic.__enter__()


    def add_field_with_default(self, model, field, default_effective_value):
        """
        Adding field with default in two separate
        operations, so we can avoid rewriting the
        whole table
        """
        with transaction.atomic():
            super(ZeroDownTimeMixin, self).add_field(model, field)
            self.add_default(model, field, default_effective_value)

    def update_existing_rows(self, model, field, default_effective_value):
        """
        Updating existing rows in table by (relatively) small batches
        to avoid long locks on table
        """
        objects_in_table = self.count_objects_in_table(model=model)
        if objects_in_table > 0:
            objects_in_batch_count = self.get_objects_in_batch_count(objects_in_table)
            while True:
                with transaction.atomic():
                    updated = self.update_batch(model=model, field=field,
                                                objects_in_batch_count=objects_in_batch_count,
                                                value=default_effective_value,
                                                )
                    print('Update {} rows in {}'.format(updated, model._meta.db_table))
                    if updated is None or updated == 0:
                        break

    def set_not_null_for_field(self, model, field, nullable):
        # If field was not null - adding
        # this knowledge to table
        if nullable is False:
            self.set_not_null(model, field)

    def get_column_info(self, model, field):
        sql = self.sql_check_column_status % {
            "table": model._meta.db_table,
            "column": field.name,
        }
        return self.get_query_result(sql)

    def get_actions_to_perform(self, model, field):
        actions = [
            'add field with default',
            'update existing rows',
            'set not null for field',
            'drop default',
        ]

        # Checking maybe this column already exists
        # if so asking user what to do next
        column_info = self.get_column_info(model, field)

        if column_info is not None:
            existed_nullable, existed_type, existed_default = column_info

            questioner = InteractiveMigrationQuestioner()
            question_template = ('It look like column "{}" in table "{}" already exist with following '
                                 'parameters: TYPE: "{}", DEFAULT: "{}", NULLABLE: "{}".'
                                 )
            question = question_template.format(field.name, model._meta.db_table,
                                                existed_type, existed_default,
                                                existed_nullable,
                                                )
            choices = ('abort migration',
                       'drop column and run migration from beginning',
                       'manually choose action to start from',
                       'show how many rows still need to be updated',
                       'mark operation as successful and proceed to next operation',
                       )

            result = questioner._choice_input(question, choices)
            if result == 1:
                sys.exit(1)
            elif result == 2:
                self.remove_field(model, field)
            elif result == 3:
                question = 'Now choose from which action process should continue'
                result = questioner._choice_input(question, actions)
                actions = actions[result-1:]
            elif result == 4:
                question = 'Rows in table where column is null: "{}"'
                need_to_update = self.need_to_update(model=model, field=field)
                questioner._choice_input(question.format(need_to_update),
                                         ('Continue', )
                                         )
                return self.get_actions_to_perform(model, field)
            elif result == 5:
                actions = []
        return actions

    def get_pk_column_name(self, model):
        return model._meta.pk.name

    def update_batch(self, model, field, objects_in_batch_count, value):
        pk_column_name = self.get_pk_column_name(model)
        sql = self.sql_update_batch % {
            "table": model._meta.db_table,
            "column": field.name,
            "batch_size": objects_in_batch_count,
            "pk_column_name": pk_column_name,
            "value": "%s",
        }
        params = [value]
        return self.get_query_result(sql, params, row_count=True)

    def get_objects_in_batch_count(self, model_count):
        """
        Calculate batch size

        :param model_count: int
        :return: int
        """
        if model_count > 500000:
            value = 10000
        else:
            value = int((model_count / 100) * 5)
        return max(1000, value)

    def get_query_result(self, sql, params=(), row_count=False):
        """
        Default django backend execute function does not
        return any result so we use this custom where needed
        """
        if self.collect_sql:
            # in collect_sql case use django function logic
            return self.execute(sql, params)

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            if row_count:
                return cursor.rowcount
            return cursor.fetchone()

    def parse_cursor_result(self, cursor, place=0, collect_sql_value=1,):
        if self.collect_sql:
            result = collect_sql_value  # For sqlmigrate purpose
        else:
            result = cursor[place]
        return result

    def execute_table_query(self, sql, model):
        sql = sql % {
            "table": model._meta.db_table
        }
        cursor = self.get_query_result(sql)
        return self.parse_cursor_result(cursor=cursor)

    def count_objects_in_table(self, model):
        count = self.execute_table_query(sql=self.sql_estimate_count_in_table,
                                         model=model,
                                         )
        if count == 0:
            # Check, maybe statistic is outdated?
            # Because previous count return 0 it will be fast query
            count = self.execute_table_query(sql=self.sql_count_in_table,
                                             model=model,
                                             )
        return count

    def need_to_update(self, model, field):
        sql = self.sql_count_in_table_with_null % {
            "table": model._meta.db_table,
            "column": field.name,
        }
        cursor = self.get_query_result(sql)
        return self.parse_cursor_result(cursor=cursor)

    def drop_default(self, model, field):
        set_default_sql, params = self._alter_column_default_sql(field, drop=True)
        self.execute_alter_column(model, set_default_sql, params)

    def add_default(self, model, field, default_value):
        set_default_sql, params = self._alter_column_default_sql(field, default_value)
        self.execute_alter_column(model, set_default_sql, params)

    def set_not_null(self, model, field):
        set_not_null_sql = self.generate_set_not_null(field)
        self.execute_alter_column(model, set_not_null_sql)

    def execute_alter_column(self, model, changes_sql, params=()):
        sql = self.sql_alter_column % {
            "table": self.quote_name(model._meta.db_table),
            "changes": changes_sql,
        }
        self.execute(sql, params)

    def generate_set_not_null(self, field):
        new_db_params = field.db_parameters(connection=self.connection)
        sql = self.sql_alter_column_not_null
        return sql % {
                'column': self.quote_name(field.column),
                'type': new_db_params['type'],
        }

    def _alter_column_default_sql(self, field, default_value=None, drop=False):
        """
        Copy this method from django2.0
        https://github.com/django/django/blob/master/django/db/backends/base/schema.py#L787
        """
        default = '%s'
        params = [default_value]

        if drop:
            params = []

        new_db_params = field.db_parameters(connection=self.connection)
        sql = self.sql_alter_column_no_default if drop else self.sql_alter_column_default
        return (
            sql % {
                'column': self.quote_name(field.column),
                'type': new_db_params['type'],
                'default': default,
            },
            params,
        )

    def execute(self, sql, params=()):
        exit_atomic = False
        # Account for non-string statement objects.
        sql = str(sql)

        if 'CREATE INDEX' in sql:
            exit_atomic = True
            sql = sql.replace('CREATE INDEX', 'CREATE INDEX CONCURRENTLY')
        atomic = self.connection.in_atomic_block
        if exit_atomic and atomic:
            self.atomic.__exit__(None, None, None)

        super(ZeroDownTimeMixin, self).execute(sql, params)

        if exit_atomic and atomic:
            self.atomic = transaction.atomic(self.connection.alias)
            self.atomic.__enter__()


class DatabaseSchemaEditor(ZeroDownTimeMixin, BaseEditor):
    pass
