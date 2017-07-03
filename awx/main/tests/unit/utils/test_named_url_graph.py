# -*- coding: utf-8 -*-
import pytest
import mock
import random

from django.db import models
from django.contrib.contenttypes.models import ContentType

from awx.main.utils.named_url_graph import generate_graph
from awx.main.models.base import CommonModel, CommonModelNameNotUnique


@pytest.fixture
def common_model_class_mock():
    def class_generator(plural):
        class ModelClass(CommonModel):

            class Meta:
                verbose_name_plural = plural
            pass
        return ModelClass
    return class_generator


@pytest.fixture
def common_model_name_not_unique_class_mock():
    def class_generator(ut, fk_a_obj, fk_b_obj, plural, soft_ut=[]):
        class ModelClass(CommonModelNameNotUnique):

            SOFT_UNIQUE_TOGETHER = soft_ut

            class Meta:
                unique_together = ut
                verbose_name_plural = plural

            fk_a = models.ForeignKey(
                fk_a_obj,
                null=True,
                on_delete=models.CASCADE,
            )
            fk_b = models.ForeignKey(
                fk_b_obj,
                null=True,
                on_delete=models.CASCADE,
            )
            str_with_choices_a = models.CharField(
                choices=("foo", "bar")
            )
            str_with_choices_b = models.CharField(
                choices=("foo", "bar")
            )
            integer = models.IntegerField()
            str_without_choices = models.CharField()
        return ModelClass
    return class_generator


@pytest.fixture
def settings_mock():
    class settings_class(object):
        pass
    return settings_class


@pytest.mark.parametrize("unique_together", [
    ("name", "str_without_choices"),
    ("name", "str_with_choices_a", 'str_without_choices'),
    ("name", "str_with_choices_a", 'integer'),
    ("name", "fk_a"),
    ("name", "fk_b"),
])
def test_invalid_generation(common_model_name_not_unique_class_mock,
                            common_model_class_mock, settings_mock, unique_together):
    models = []
    valid_parent_out_of_range = common_model_class_mock('valid_parent_out_of_range')
    invalid_parent = common_model_name_not_unique_class_mock(
        ('integer', 'name'),
        valid_parent_out_of_range,
        valid_parent_out_of_range,
        'invalid_parent',
    )
    models.append(invalid_parent)
    model_1 = common_model_name_not_unique_class_mock(
        unique_together,
        invalid_parent,
        valid_parent_out_of_range,
        'model_1'
    )
    models.append(model_1)

    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)
    assert not settings_mock.NAMED_URL_FORMATS


def test_soft_unique_together_being_included(common_model_name_not_unique_class_mock,
                                             common_model_class_mock, settings_mock):
    models = []
    model_1 = common_model_class_mock('model_1')
    models.append(model_1)
    model_2 = common_model_name_not_unique_class_mock(
        (),
        model_1,
        model_1,
        'model_2',
        soft_ut=[('name', 'fk_a')]
    )
    models.append(model_2)

    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)
    assert settings_mock.NAMED_URL_GRAPH[model_1].model == model_1
    assert settings_mock.NAMED_URL_GRAPH[model_1].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[model_1].adj_list == []

    assert settings_mock.NAMED_URL_GRAPH[model_2].model == model_2
    assert settings_mock.NAMED_URL_GRAPH[model_2].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_2].adj_list)[0] == ('fk_a',)
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_2].adj_list)[1]] == [model_1]


def test_chain_generation(common_model_class_mock, common_model_name_not_unique_class_mock, settings_mock):
    """
    Graph topology:

     model_3
        |
        | fk_a
        |
        V
     model_2
        |
        | fk_a
        |
        V
     model_1
    """
    models = []
    model_1 = common_model_class_mock('model_1')
    models.append(model_1)
    model_2 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a'),
        model_1,
        model_1,
        'model_2',
    )
    models.append(model_2)
    model_3 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a'),
        model_2,
        model_1,
        'model_3',
    )
    models.append(model_3)

    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)

    assert settings_mock.NAMED_URL_GRAPH[model_1].model == model_1
    assert settings_mock.NAMED_URL_GRAPH[model_1].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[model_1].adj_list == []

    assert settings_mock.NAMED_URL_GRAPH[model_2].model == model_2
    assert settings_mock.NAMED_URL_GRAPH[model_2].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_2].adj_list)[0] == ('fk_a',)
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_2].adj_list)[1]] == [model_1]

    assert settings_mock.NAMED_URL_GRAPH[model_3].model == model_3
    assert settings_mock.NAMED_URL_GRAPH[model_3].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_3].adj_list)[0] == ('fk_a',)
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_3].adj_list)[1]] == [model_2]


def test_graph_generation(common_model_class_mock, common_model_name_not_unique_class_mock, settings_mock):
    """
    Graph topology:

                model_1
                   /\
             fk_a /  \ fk_b
                 /    \
                V      V
          model_2_1   model_2_2
               /\fk_b /\
         fk_a /  \   /  \ fk_b
             /    \ /fk_a\
            V      V      V
     model_3_1 model_3_2 model_3_3
    """
    models = []
    model_3_1 = common_model_class_mock('model_3_1')
    models.append(model_3_1)
    model_3_2 = common_model_class_mock('model_3_2')
    models.append(model_3_2)
    model_3_3 = common_model_class_mock('model_3_3')
    models.append(model_3_3)
    model_2_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_b', 'fk_a'),
        model_3_1,
        model_3_2,
        'model_2_1',
    )
    models.append(model_2_1)
    model_2_2 = common_model_name_not_unique_class_mock(
        ('name', 'fk_b', 'fk_a'),
        model_3_2,
        model_3_3,
        'model_2_2',
    )
    models.append(model_2_2)
    model_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a', 'fk_b'),
        model_2_1,
        model_2_2,
        'model_1',
    )
    models.append(model_1)
    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)

    assert settings_mock.NAMED_URL_GRAPH[model_1].model == model_1
    assert settings_mock.NAMED_URL_GRAPH[model_1].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_1].adj_list)[0] == ('fk_a', 'fk_b')
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_1].adj_list)[1]] == [model_2_1, model_2_2]

    assert settings_mock.NAMED_URL_GRAPH[model_2_1].model == model_2_1
    assert settings_mock.NAMED_URL_GRAPH[model_2_1].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_2_1].adj_list)[0] == ('fk_a', 'fk_b')
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_2_1].adj_list)[1]] == [model_3_1, model_3_2]

    assert settings_mock.NAMED_URL_GRAPH[model_2_2].model == model_2_2
    assert settings_mock.NAMED_URL_GRAPH[model_2_2].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_2_2].adj_list)[0] == ('fk_a', 'fk_b')
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_2_2].adj_list)[1]] == [model_3_2, model_3_3]

    assert settings_mock.NAMED_URL_GRAPH[model_3_1].model == model_3_1
    assert settings_mock.NAMED_URL_GRAPH[model_3_1].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[model_3_1].adj_list == []

    assert settings_mock.NAMED_URL_GRAPH[model_3_2].model == model_3_2
    assert settings_mock.NAMED_URL_GRAPH[model_3_2].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[model_3_2].adj_list == []

    assert settings_mock.NAMED_URL_GRAPH[model_3_3].model == model_3_3
    assert settings_mock.NAMED_URL_GRAPH[model_3_3].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[model_3_3].adj_list == []


def test_largest_graph_is_generated(common_model_name_not_unique_class_mock,
                                    common_model_class_mock, settings_mock):
    """
    Graph topology:

            model_1
               |
               | fk_a
               |
               V
            model_2
            /     \
      fk_b /       \ fk_a
          /         \
         V           V
    valid_model invalid_model
    """
    models = []
    valid_model = common_model_class_mock('valid_model')
    models.append(valid_model)
    invalid_model = common_model_class_mock('invalid_model')
    model_2 = common_model_name_not_unique_class_mock(
        (('name', 'fk_a'), ('name', 'fk_b')),
        invalid_model,
        valid_model,
        'model_2',
    )
    models.append(model_2)
    model_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a'),
        model_2,
        model_2,
        'model_1',
    )
    models.append(model_1)

    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)

    assert settings_mock.NAMED_URL_GRAPH[model_1].model == model_1
    assert settings_mock.NAMED_URL_GRAPH[model_1].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_1].adj_list)[0] == ('fk_a',)
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_1].adj_list)[1]] == [model_2]

    assert settings_mock.NAMED_URL_GRAPH[model_2].model == model_2
    assert settings_mock.NAMED_URL_GRAPH[model_2].fields == ('name',)
    assert zip(*settings_mock.NAMED_URL_GRAPH[model_2].adj_list)[0] == ('fk_b',)
    assert [x.model for x in zip(*settings_mock.NAMED_URL_GRAPH[model_2].adj_list)[1]] == [valid_model]

    assert settings_mock.NAMED_URL_GRAPH[valid_model].model == valid_model
    assert settings_mock.NAMED_URL_GRAPH[valid_model].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[valid_model].adj_list == []

    assert invalid_model not in settings_mock.NAMED_URL_GRAPH


def test_contenttype_being_ignored(common_model_name_not_unique_class_mock, settings_mock):
    model = common_model_name_not_unique_class_mock(
        ('name', 'fk_a'),
        ContentType,
        ContentType,
        'model',
    )
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph([model])
    assert settings_mock.NAMED_URL_GRAPH[model].model == model
    assert settings_mock.NAMED_URL_GRAPH[model].fields == ('name',)
    assert settings_mock.NAMED_URL_GRAPH[model].adj_list == []


@pytest.mark.parametrize('input_, output', [
    ('alice++bob+foo++cat++dog', {
        'name': 'alice',
        'fk_a__name': 'bob',
        'fk_a__str_with_choices_a': 'foo',
        'fk_b__name': 'dog',
        'fk_a__fk_a__name': 'cat',
    }),
    ('alice++++dog', {
        'name': 'alice',
        'fk_b__name': 'dog',
    }),
    ('alice++bob+foo++cat++', {
        'name': 'alice',
        'fk_a__name': 'bob',
        'fk_a__str_with_choices_a': 'foo',
        'fk_a__fk_a__name': 'cat',
    }),
    ('alice++bob+foo++++dog', {
        'name': 'alice',
        'fk_a__name': 'bob',
        'fk_a__str_with_choices_a': 'foo',
        'fk_b__name': 'dog',
    }),
])
def test_populate_named_url_query_kwargs(common_model_name_not_unique_class_mock,
                                         common_model_class_mock, settings_mock,
                                         input_, output):
    """
    graph topology:

         model_1
            |   \
       fk_a |    \ fk_b
            |     \
            v      v
        model_2_1 model_2_2
            |
            | fk_a
            |
            v
         model_3
    """
    models = []
    model_3 = common_model_class_mock('model_3')
    models.append(model_3)
    model_2_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a', 'str_with_choices_a'),
        model_3,
        model_3,
        'model_2_1',
    )
    models.append(model_2_1)
    model_2_2 = common_model_class_mock('model_2_2')
    models.append(model_2_2)
    model_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a', 'fk_b'),
        model_2_1,
        model_2_2,
        'model_1',
    )
    models.append(model_1)
    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)
    kwargs = {}
    assert settings_mock.NAMED_URL_GRAPH[model_1].populate_named_url_query_kwargs(kwargs, input_)
    assert kwargs == output


@pytest.mark.parametrize('input_', [
    '4399',
    'alice-foo',
    'alice--bob',
    'alice-foo--bob--cat',
    'alice-foo--bob-',
])
def test_populate_named_url_invalid_query_kwargs(common_model_name_not_unique_class_mock,
                                                 common_model_class_mock, settings_mock,
                                                 input_):
    models = []
    model_2 = common_model_class_mock('model_2')
    models.append(model_2)
    model_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a', 'str_with_choices_a'),
        model_2,
        model_2,
        'model_1',
    )
    models.append(model_1)
    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)
    kwargs = {}
    assert not settings_mock.NAMED_URL_GRAPH[model_1].populate_named_url_query_kwargs(kwargs, input_)


def test_reserved_uri_char_decoding(common_model_class_mock, settings_mock):
    model = common_model_class_mock('model')
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph([model])
    kwargs = {}
    settings_mock.NAMED_URL_GRAPH[model].populate_named_url_query_kwargs(kwargs, r"%3B%2F%3F%3A%40%3D%26[+]")
    assert kwargs == {'name': ';/?:@=&+'}


def test_unicode_decoding(common_model_class_mock, settings_mock):
    model = common_model_class_mock('model')
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph([model])
    kwargs = {}
    settings_mock.NAMED_URL_GRAPH[model].populate_named_url_query_kwargs(
        kwargs, r"%E6%88%91%E4%B8%BA%E6%88%91%E8%9B%A4%E7%BB%AD1s"
    )
    assert kwargs == {'name': u'我为我蛤续1s'}


def test_generate_named_url(common_model_name_not_unique_class_mock,
                            common_model_class_mock, settings_mock):
    """
    graph topology:

         model_1
            |   \
       fk_a |    \ fk_b
            |     \
            v      v
        model_2_1 model_2_2
            |
            | fk_a
            |
            v
         model_3
    """
    models = []
    model_3 = common_model_class_mock('model_3')
    models.append(model_3)
    model_2_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a', 'str_with_choices_a'),
        model_3,
        model_3,
        'model_2_1',
    )
    models.append(model_2_1)
    model_2_2 = common_model_class_mock('model_2_2')
    models.append(model_2_2)
    model_1 = common_model_name_not_unique_class_mock(
        ('name', 'fk_a', 'fk_b'),
        model_2_1,
        model_2_2,
        'model_1',
    )
    models.append(model_1)
    random.shuffle(models)
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph(models)
    obj_3 = model_3(name='cat')
    obj_2_2 = model_2_2(name='dog')
    obj_2_1 = model_2_1(name='bob', str_with_choices_a='foo', fk_a=obj_3)
    obj_1 = model_1(name='alice', fk_a=obj_2_1, fk_b=obj_2_2)
    obj_1.fk_b = None
    assert settings_mock.NAMED_URL_GRAPH[model_1].generate_named_url(obj_1) == 'alice++bob+foo++cat++'
    obj_1.fk_b = obj_2_2
    assert settings_mock.NAMED_URL_GRAPH[model_1].generate_named_url(obj_1) == 'alice++bob+foo++cat++dog'
    obj_2_1.fk_a = None
    assert settings_mock.NAMED_URL_GRAPH[model_1].generate_named_url(obj_1) == 'alice++bob+foo++++dog'
    obj_1.fk_a = None
    assert settings_mock.NAMED_URL_GRAPH[model_1].generate_named_url(obj_1) == 'alice++++dog'
    obj_1.fk_b = None
    assert settings_mock.NAMED_URL_GRAPH[model_1].generate_named_url(obj_1) == 'alice++++'


def test_reserved_uri_char_encoding(common_model_class_mock, settings_mock):
    model = common_model_class_mock('model')
    with mock.patch('awx.main.utils.named_url_graph.settings', settings_mock):
        generate_graph([model])
    obj = model(name=u';/?:@=&+我为我蛤续1s')
    assert settings_mock.NAMED_URL_GRAPH[model].generate_named_url(obj) == u"%3B%2F%3F%3A%40%3D%26[+]我为我蛤续1s"
