# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import re
import sys
import six
from pyparsing import infixNotation, opAssoc, Optional, Literal, CharsNotIn

# Django
from django.db.models.signals import (
    post_save,
    post_delete,
)
from django.db.models.signals import m2m_changed
from django.db import models
from django.db.models.fields.related import (
    add_lazy_relation,
    SingleRelatedObjectDescriptor,
    ReverseSingleRelatedObjectDescriptor,
    ManyRelatedObjectsDescriptor,
    ReverseManyRelatedObjectsDescriptor,
)
from django.utils.encoding import smart_text
from django.db.models import Q

# Django-JSONField
from jsonfield import JSONField as upstream_JSONField
from jsonbfield.fields import JSONField as upstream_JSONBField

# AWX
from awx.main.models.rbac import batch_role_ancestor_rebuilding, Role
from awx.main.utils import get_current_apps


__all__ = ['AutoOneToOneField', 'ImplicitRoleField', 'JSONField', 'DynamicFilterField']


class JSONField(upstream_JSONField):

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection, context):
        if value in {'', None} and not self.null:
            return {}
        return super(JSONField, self).from_db_value(value, expression, connection, context)


class JSONBField(upstream_JSONBField):
    def get_db_prep_value(self, value, connection, prepared=False):
        if connection.vendor == 'sqlite':
            # sqlite (which we use for tests) does not support jsonb;
            return json.dumps(value)
        return super(JSONBField, self).get_db_prep_value(
            value, connection, prepared
        )

    def from_db_value(self, value, expression, connection, context):
        # Work around a bug in django-jsonfield
        # https://bitbucket.org/schinckel/django-jsonfield/issues/57/cannot-use-in-the-same-project-as-djangos
        if isinstance(value, six.string_types):
            return json.loads(value)
        return value

# Based on AutoOneToOneField from django-annoying:
# https://bitbucket.org/offline/django-annoying/src/a0de8b294db3/annoying/fields.py


class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor):
    """Descriptor for access to the object from its related class."""

    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoSingleRelatedObjectDescriptor,
                         self).__get__(instance, instance_type)
        except self.related.related_model.DoesNotExist:
            obj = self.related.related_model(**{self.related.field.name: instance})
            if self.related.field.rel.parent_link:
                raise NotImplementedError('not supported with polymorphic!')
                for f in instance._meta.local_fields:
                    setattr(obj, f.name, getattr(instance, f.name))
            obj.save()
            return obj


class AutoOneToOneField(models.OneToOneField):
    """OneToOneField that creates related object if it doesn't exist."""

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(),
                AutoSingleRelatedObjectDescriptor(related))


def resolve_role_field(obj, field):
    ret = []

    field_components = field.split('.', 1)
    if hasattr(obj, field_components[0]):
        obj = getattr(obj, field_components[0])
    else:
        return []

    if obj is None:
        return []

    if len(field_components) == 1:
        role_cls = str(get_current_apps().get_model('main', 'Role'))
        if not str(type(obj)) == role_cls:
            raise Exception(smart_text('{} refers to a {}, not a Role'.format(field, type(obj))))
        ret.append(obj.id)
    else:
        if type(obj) is ManyRelatedObjectsDescriptor:
            for o in obj.all():
                ret += resolve_role_field(o, field_components[1])
        else:
            ret += resolve_role_field(obj, field_components[1])

    return ret


def is_implicit_parent(parent_role, child_role):
    '''
    Determine if the parent_role is an implicit parent as defined by
    the model definition. This does not include any role parents that
    might have been set by the user.
    '''
    # Get the list of implicit parents that were defined at the class level.
    implicit_parents = getattr(
        child_role.content_object.__class__, child_role.role_field
    ).field.parent_role
    if type(implicit_parents) != list:
        implicit_parents = [implicit_parents]

    # Check to see if the role matches any in the implicit parents list
    for implicit_parent_path in implicit_parents:
        if implicit_parent_path.startswith('singleton:'):
            # Singleton role isn't an object role, `singleton_name` uniquely identifies it
            if parent_role.is_singleton() and parent_role.singleton_name == implicit_parent_path[10:]:
                return True
        else:
            # Walk over multiple related objects to obtain the implicit parent
            related_obj = child_role.content_object
            for next_field in implicit_parent_path.split('.'):
                related_obj = getattr(related_obj, next_field)
                if related_obj is None:
                    break
            if related_obj and parent_role == related_obj:
                return True
    return False


class ImplicitRoleDescriptor(ReverseSingleRelatedObjectDescriptor):
    pass


class ImplicitRoleField(models.ForeignKey):
    """Implicitly creates a role entry for a resource"""

    def __init__(self, parent_role=None, *args, **kwargs):
        self.parent_role = parent_role

        kwargs.setdefault('to', 'Role')
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('null', 'True')
        super(ImplicitRoleField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ImplicitRoleField, self).deconstruct()
        kwargs['parent_role'] = self.parent_role
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name):
        super(ImplicitRoleField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ImplicitRoleDescriptor(self))

        if not hasattr(cls, '__implicit_role_fields'):
            setattr(cls, '__implicit_role_fields', [])
        getattr(cls, '__implicit_role_fields').append(self)

        post_save.connect(self._post_save, cls, True, dispatch_uid='implicit-role-post-save')
        post_delete.connect(self._post_delete, cls, True, dispatch_uid='implicit-role-post-delete')
        add_lazy_relation(cls, self, "self", self.bind_m2m_changed)

    def bind_m2m_changed(self, _self, _role_class, cls):
        if not self.parent_role:
            return

        field_names = self.parent_role
        if type(field_names) is not list:
            field_names = [field_names]

        for field_name in field_names:
            # Handle the OR syntax for role parents
            if type(field_name) == tuple:
                continue

            if field_name.startswith('singleton:'):
                continue

            field_name, sep, field_attr = field_name.partition('.')
            field = getattr(cls, field_name)

            if type(field) is ReverseManyRelatedObjectsDescriptor or \
               type(field) is ManyRelatedObjectsDescriptor:

                if '.' in field_attr:
                    raise Exception('Referencing deep roles through ManyToMany fields is unsupported.')

                if type(field) is ReverseManyRelatedObjectsDescriptor:
                    sender = field.through
                else:
                    sender = field.related.through

                reverse = type(field) is ManyRelatedObjectsDescriptor
                m2m_changed.connect(self.m2m_update(field_attr, reverse), sender, weak=False)

    def m2m_update(self, field_attr, _reverse):
        def _m2m_update(instance, action, model, pk_set, reverse, **kwargs):
            if action == 'post_add' or action == 'pre_remove':
                if _reverse:
                    reverse = not reverse

                if reverse:
                    for pk in pk_set:
                        obj = model.objects.get(pk=pk)
                        if action == 'post_add':
                            getattr(instance, field_attr).children.add(getattr(obj, self.name))
                        if action == 'pre_remove':
                            getattr(instance, field_attr).children.remove(getattr(obj, self.name))

                else:
                    for pk in pk_set:
                        obj = model.objects.get(pk=pk)
                        if action == 'post_add':
                            getattr(instance, self.name).parents.add(getattr(obj, field_attr))
                        if action == 'pre_remove':
                            getattr(instance, self.name).parents.remove(getattr(obj, field_attr))
        return _m2m_update


    def _post_save(self, instance, created, *args, **kwargs):
        Role_ = get_current_apps().get_model('main', 'Role')
        ContentType_ = get_current_apps().get_model('contenttypes', 'ContentType')
        ct_id = ContentType_.objects.get_for_model(instance).id
        with batch_role_ancestor_rebuilding():
            # Create any missing role objects
            missing_roles = []
            for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
                cur_role = getattr(instance, implicit_role_field.name, None)
                if cur_role is None:
                    missing_roles.append(
                        Role_(
                            role_field=implicit_role_field.name,
                            content_type_id=ct_id,
                            object_id=instance.id
                        )
                    )
            if len(missing_roles) > 0:
                Role_.objects.bulk_create(missing_roles)
                updates = {}
                role_ids = []
                for role in Role_.objects.filter(content_type_id=ct_id, object_id=instance.id):
                    setattr(instance, role.role_field, role)
                    updates[role.role_field] = role.id
                    role_ids.append(role.id)
                type(instance).objects.filter(pk=instance.pk).update(**updates)
                Role.rebuild_role_ancestor_list(role_ids, [])

            # Update parentage if necessary
            for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
                cur_role = getattr(instance, implicit_role_field.name)
                original_parents = set(json.loads(cur_role.implicit_parents))
                new_parents = implicit_role_field._resolve_parent_roles(instance)
                cur_role.parents.remove(*list(original_parents - new_parents))
                cur_role.parents.add(*list(new_parents - original_parents))
                new_parents_list = list(new_parents)
                new_parents_list.sort()
                new_parents_json = json.dumps(new_parents_list)
                if cur_role.implicit_parents != new_parents_json:
                    cur_role.implicit_parents = new_parents_json
                    cur_role.save()


    def _resolve_parent_roles(self, instance):
        if not self.parent_role:
            return set()

        paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
        parent_roles = set()

        for path in paths:
            if path.startswith("singleton:"):
                singleton_name = path[10:]
                Role_ = get_current_apps().get_model('main', 'Role')
                qs = Role_.objects.filter(singleton_name=singleton_name)
                if qs.count() >= 1:
                    role = qs[0]
                else:
                    role = Role_.objects.create(singleton_name=singleton_name, role_field=singleton_name)
                parents = [role.id]
            else:
                parents = resolve_role_field(instance, path)

            for parent in parents:
                parent_roles.add(parent)
        return parent_roles

    def _post_delete(self, instance, *args, **kwargs):
        role_ids = []
        for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
            role_ids.append(getattr(instance, implicit_role_field.name + '_id'))

        Role_ = get_current_apps().get_model('main', 'Role')
        child_ids = [x for x in Role_.parents.through.objects.filter(to_role_id__in=role_ids).distinct().values_list('from_role_id', flat=True)]
        Role_.objects.filter(id__in=role_ids).delete()
        Role.rebuild_role_ancestor_list([], child_ids)


unicode_spaces = [unichr(c) for c in xrange(sys.maxunicode) if unichr(c).isspace()]
unicode_spaces_other = unicode_spaces + [u'(', u')', u'=', u'"']


def string_to_type(t):
    if t == u'true':
        return True
    elif t == u'false':
        return False

    if re.search('^[-+]?[0-9]+$',t):
        return int(t)

    if re.search('^[-+]?[0-9]+\.[0-9]+$',t):
        return float(t)

    return t


class DynamicFilterField(models.TextField):


    class BoolOperand(object):
        def __init__(self, t):
            kwargs = dict()
            k, v = self._extract_key_value(t)
            k, v = self._json_path_to_contains(k, v)
            kwargs[k] = v
            self.result = Q(**kwargs)

        '''
        TODO: We should be able to express this in the grammar and let 
              pyparsing do the heavy lifting.
        TODO: separate django filter requests from our custom json filter
              request so we don't process the key any. This could be
              accomplished using a whitelist or introspecting the
              relationship refered to to see if it's a jsonb type.
        '''
        def _json_path_to_contains(self, k, v):
            pieces = k.split('__')

            flag_first_arr_found = False

            assembled_k = ''
            assembled_v = v

            last_kv = None
            last_v = None

            contains_count = 0
            for i, piece in enumerate(pieces):
                if flag_first_arr_found is False and piece.endswith('[]'):
                    assembled_k += u'%s__contains' % (piece[0:-2])
                    contains_count += 1
                    flag_first_arr_found = True
                elif flag_first_arr_found is False and i == len(pieces) - 1:
                    assembled_k += u'%s' % piece
                elif flag_first_arr_found is False:
                    assembled_k += u'%s__' % piece
                elif flag_first_arr_found is True:
                    new_kv = dict()
                    if piece.endswith('[]'):
                        new_v = []
                        new_kv[piece[0:-2]] = new_v
                    else:
                        new_v = dict()
                        new_kv[piece] = new_v


                    if last_v is None:
                        last_v = []
                        assembled_v = last_v

                    if type(last_v) is list:
                        last_v.append(new_kv)
                    elif type(last_v) is dict:
                        last_kv[last_kv.keys()[0]] = new_kv

                    last_v = new_v
                    last_kv = new_kv
                    contains_count += 1

            '''
            Explicit quotes are kept up till this point.
            They will be kept if there is ONLY ONE [] in the key search.
            This is because django filter + postgres expect strings to be
            quoted "\"hello_world\"". If, instead, there are many [] in a
            filter key then we can remove the " and ".
            '''
            if contains_count != 1:
                if type(v) is unicode and v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                if contains_count == 0:
                    assembled_v = v

            if contains_count > 1:
                if type(last_v) is list:
                    last_v.append(v)
                if type(last_v) is dict:
                    last_kv[last_kv.keys()[0]] = v

            return (assembled_k, assembled_v)

        def _extract_key_value(self, t):
            t_len = len(t)

            k = None
            v = None

            # key
            # "something"=
            v_offset = 2
            if t_len >= 2 and t[0] == "\"" and t[2] == "\"":
                k = t[1]
                v_offset = 4
            # something=
            else:
                k = t[0]

            # value
            # ="something"
            if t_len > (v_offset + 2) and t[v_offset] == "\"" and t[v_offset + 2] == "\"":
                v = u'"' + unicode(t[v_offset + 1]) + u'"'
                #v = t[v_offset + 1]
            # empty ""
            elif t_len > (v_offset + 1):
                v = u""
            # no ""
            else:
                v = string_to_type(t[v_offset])

            return (k, v)


    class BoolBinOp(object):
        def __init__(self, t):
            self.left = t[0][0].result
            self.right = t[0][2].result

            self.result = self.execute_logic(self.left, self.right)


    class BoolAnd(BoolBinOp):
        def execute_logic(self, left, right):
            return left & right


    class BoolOr(BoolBinOp):
        def execute_logic(self, left, right):
            return left | right


    class BoolNot(object):
        def __init__(self,t):
            self.right = t[0][1]
            self.result = ~self.right


    @classmethod
    def filter_string_to_q(cls, filter_string):

        '''
        TODO:
        * handle values with " via: a.b.c.d="hello\"world"
        * handle keys with " via: a.\"b.c="yeah"
        * handle key with __ in it

        * add not support

        * transform [] into contains via: a.b.c[].d[].e.f[]="blah"

        * handle optional value quoted: a.b.c=""

        '''
        filter_string = unicode(filter_string)

        atom = CharsNotIn(unicode_spaces_other)
        atom_inside_quotes = CharsNotIn(u'"')
        atom_quoted = Literal('"') + Optional(atom_inside_quotes) + Literal('"')
        EQUAL = Literal('=')

        grammar = ((atom_quoted | atom) + EQUAL + Optional((atom_quoted | atom)))
        grammar.setParseAction(cls.BoolOperand)

        boolExpr = infixNotation(grammar, [
            #("not", 1, opAssoc.RIGHT, cls.BoolNot),
            ("and", 2, opAssoc.LEFT, cls.BoolAnd),
            ("or",  2, opAssoc.LEFT, cls.BoolOr),
        ])

        res = boolExpr.parseString('(' + filter_string + ')')
        if len(res) > 0:
            return res[0].result

        raise RuntimeError("Parsing the filter_string %s went terribly wrong" % filter_string)


