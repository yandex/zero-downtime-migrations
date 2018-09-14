# coding: utf-8

from __future__ import unicode_literals

import pytest

from test_app.models import TestModel


@pytest.fixture
def test_object():
    return TestModel.objects.create(name='some name')


@pytest.fixture
def test_object_two():
    return TestModel.objects.create(name='some other name')


@pytest.fixture
def test_object_three():
    return TestModel.objects.create(name='some different name')
