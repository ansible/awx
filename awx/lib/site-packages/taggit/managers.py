from __future__ import unicode_literals

from django import VERSION
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields import Field
from django.db.models.fields.related import ManyToManyRel, RelatedField, add_lazy_relation
from django.db.models.related import RelatedObject
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from django.utils import six

try:
    from django.db.models.related import PathInfo
except ImportError:
    pass  # PathInfo is not used on Django < 1.6

from taggit.forms import TagField
from taggit.models import TaggedItem, GenericTaggedItemBase
from taggit.utils import require_instance_manager


def _model_name(model):
    if VERSION < (1, 7):
        return model._meta.module_name
    else:
        return model._meta.model_name


class TaggableRel(ManyToManyRel):
    def __init__(self, field):
        self.related_name = None
        self.limit_choices_to = {}
        self.symmetrical = True
        self.multiple = True
        self.through = None
        self.field = field

    def get_joining_columns(self):
        return self.field.get_reverse_joining_columns()

    def get_extra_restriction(self, where_class, alias, related_alias):
        return self.field.get_extra_restriction(where_class, related_alias, alias)


class ExtraJoinRestriction(object):
    """
    An extra restriction used for contenttype restriction in joins.
    """
    def __init__(self, alias, col, content_types):
        self.alias = alias
        self.col = col
        self.content_types = content_types

    def as_sql(self, qn, connection):
        if len(self.content_types) == 1:
            extra_where = "%s.%s = %%s" % (qn(self.alias), qn(self.col))
            params = [self.content_types[0]]
        else:
            extra_where = "%s.%s IN (%s)" % (qn(self.alias), qn(self.col),
                                             ','.join(['%s'] * len(self.content_types)))
            params = self.content_types
        return extra_where, params

    def relabel_aliases(self, change_map):
        self.alias = change_map.get(self.alias, self.alias)


class TaggableManager(RelatedField, Field):
    def __init__(self, verbose_name=_("Tags"),
        help_text=_("A comma-separated list of tags."), through=None, blank=False):
        Field.__init__(self, verbose_name=verbose_name, help_text=help_text, blank=blank)
        self.through = through or TaggedItem
        self.rel = TaggableRel(self)

    def __get__(self, instance, model):
        if instance is not None and instance.pk is None:
            raise ValueError("%s objects need to have a primary key value "
                "before you can access their tags." % model.__name__)
        manager = _TaggableManager(
            through=self.through, model=model, instance=instance
        )
        return manager

    def contribute_to_class(self, cls, name):
        if VERSION < (1, 7):
            self.name = self.column = name
        else:
            self.set_attributes_from_name(name)
        self.model = cls
        cls._meta.add_field(self)
        setattr(cls, name, self)
        if not cls._meta.abstract:
            if isinstance(self.through, six.string_types):
                def resolve_related_class(field, model, cls):
                    self.through = model
                    self.post_through_setup(cls)
                add_lazy_relation(
                    cls, self, self.through, resolve_related_class
                )
            else:
                self.post_through_setup(cls)

    def __lt__(self, other):
        """
        Required contribute_to_class as Django uses bisect
        for ordered class contribution and bisect requires
        a orderable type in py3.
        """
        return False

    def post_through_setup(self, cls):
        self.related = RelatedObject(cls, self.model, self)
        self.use_gfk = (
            self.through is None or issubclass(self.through, GenericTaggedItemBase)
        )
        self.rel.to = self.through._meta.get_field("tag").rel.to
        self.related = RelatedObject(self.through, cls, self)
        if self.use_gfk:
            tagged_items = GenericRelation(self.through)
            tagged_items.contribute_to_class(cls, "tagged_items")

    def save_form_data(self, instance, value):
        getattr(instance, self.name).set(*value)

    def formfield(self, form_class=TagField, **kwargs):
        defaults = {
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
            "required": not self.blank
        }
        defaults.update(kwargs)
        return form_class(**defaults)

    def value_from_object(self, instance):
        if instance.pk:
            return self.through.objects.filter(**self.through.lookup_kwargs(instance))
        return self.through.objects.none()

    def related_query_name(self):
        return _model_name(self.model)

    def m2m_reverse_name(self):
        return self.through._meta.get_field_by_name("tag")[0].column

    def m2m_reverse_field_name(self):
        return self.through._meta.get_field_by_name("tag")[0].name

    def m2m_target_field_name(self):
        return self.model._meta.pk.name

    def m2m_reverse_target_field_name(self):
        return self.rel.to._meta.pk.name

    def m2m_column_name(self):
        if self.use_gfk:
            return self.through._meta.virtual_fields[0].fk_field
        return self.through._meta.get_field('content_object').column

    def db_type(self, connection=None):
        return None

    def m2m_db_table(self):
        return self.through._meta.db_table

    def bulk_related_objects(self, new_objs, using):
        return []

    def extra_filters(self, pieces, pos, negate):
        if negate or not self.use_gfk:
            return []
        prefix = "__".join(["tagged_items"] + pieces[:pos-2])
        get = ContentType.objects.get_for_model
        cts = [get(obj) for obj in _get_subclasses(self.model)]
        if len(cts) == 1:
            return [("%s__content_type" % prefix, cts[0])]
        return [("%s__content_type__in" % prefix, cts)]

    def get_extra_join_sql(self, connection, qn, lhs_alias, rhs_alias):
        model_name = _model_name(self.through)
        if rhs_alias == '%s_%s' % (self.through._meta.app_label, model_name):
            alias_to_join = rhs_alias
        else:
            alias_to_join = lhs_alias
        extra_col = self.through._meta.get_field_by_name('content_type')[0].column
        content_type_ids = [ContentType.objects.get_for_model(subclass).pk for subclass in _get_subclasses(self.model)]
        if len(content_type_ids) == 1:
            content_type_id = content_type_ids[0]
            extra_where = " AND %s.%s = %%s" % (qn(alias_to_join), qn(extra_col))
            params = [content_type_id]
        else:
            extra_where = " AND %s.%s IN (%s)" % (qn(alias_to_join), qn(extra_col), ','.join(['%s']*len(content_type_ids)))
            params = content_type_ids
        return extra_where, params

    def _get_mm_case_path_info(self, direct=False):
        pathinfos = []
        linkfield1 = self.through._meta.get_field_by_name('content_object')[0]
        linkfield2 = self.through._meta.get_field_by_name(self.m2m_reverse_field_name())[0]
        if direct:
            join1infos, _, _, _ = linkfield1.get_reverse_path_info()
            join2infos, opts, target, final = linkfield2.get_path_info()
        else:
            join1infos, _, _, _ = linkfield2.get_reverse_path_info()
            join2infos, opts, target, final = linkfield1.get_path_info()
        pathinfos.extend(join1infos)
        pathinfos.extend(join2infos)
        return pathinfos, opts, target, final

    def _get_gfk_case_path_info(self, direct=False):
        pathinfos = []
        from_field = self.model._meta.pk
        opts = self.through._meta
        object_id_field = opts.get_field_by_name('object_id')[0]
        linkfield = self.through._meta.get_field_by_name(self.m2m_reverse_field_name())[0]
        if direct:
            join1infos = [PathInfo(from_field, object_id_field, self.model._meta, opts, self, True, False)]
            join2infos, opts, target, final = linkfield.get_path_info()
        else:
            join1infos, _, _, _ = linkfield.get_reverse_path_info()
            join2infos = [PathInfo(object_id_field, from_field, opts, self.model._meta, self, True, False)]
            target = from_field
            final = self
            opts = self.model._meta

        pathinfos.extend(join1infos)
        pathinfos.extend(join2infos)
        return pathinfos, opts, target, final

    def get_path_info(self):
        if self.use_gfk:
            return self._get_gfk_case_path_info(direct=True)
        else:
            return self._get_mm_case_path_info(direct=True)

    def get_reverse_path_info(self):
        if self.use_gfk:
            return self._get_gfk_case_path_info(direct=False)
        else:
            return self._get_mm_case_path_info(direct=False)

    # This and all the methods till the end of class are only used in django >= 1.6
    def _get_mm_case_path_info(self, direct=False):
        pathinfos = []
        linkfield1 = self.through._meta.get_field_by_name('content_object')[0]
        linkfield2 = self.through._meta.get_field_by_name(self.m2m_reverse_field_name())[0]
        if direct:
            join1infos = linkfield1.get_reverse_path_info()
            join2infos = linkfield2.get_path_info()
        else:
            join1infos = linkfield2.get_reverse_path_info()
            join2infos = linkfield1.get_path_info()
        pathinfos.extend(join1infos)
        pathinfos.extend(join2infos)
        return pathinfos

    def _get_gfk_case_path_info(self, direct=False):
        pathinfos = []
        from_field = self.model._meta.pk
        opts = self.through._meta
        object_id_field = opts.get_field_by_name('object_id')[0]
        linkfield = self.through._meta.get_field_by_name(self.m2m_reverse_field_name())[0]
        if direct:
            join1infos = [PathInfo(self.model._meta, opts, [from_field], self.rel, True, False)]
            join2infos = linkfield.get_path_info()
        else:
            join1infos = linkfield.get_reverse_path_info()
            join2infos = [PathInfo(opts, self.model._meta, [object_id_field], self, True, False)]
        pathinfos.extend(join1infos)
        pathinfos.extend(join2infos)
        return pathinfos

    def get_path_info(self):
        if self.use_gfk:
            return self._get_gfk_case_path_info(direct=True)
        else:
            return self._get_mm_case_path_info(direct=True)

    def get_reverse_path_info(self):
        if self.use_gfk:
            return self._get_gfk_case_path_info(direct=False)
        else:
            return self._get_mm_case_path_info(direct=False)

    def get_joining_columns(self, reverse_join=False):
        if reverse_join:
            return (("id", "object_id"),)
        else:
            return (("object_id", "id"),)

    def get_extra_restriction(self, where_class, alias, related_alias):
        extra_col = self.through._meta.get_field_by_name('content_type')[0].column
        content_type_ids = [ContentType.objects.get_for_model(subclass).pk
                            for subclass in _get_subclasses(self.model)]
        return ExtraJoinRestriction(related_alias, extra_col, content_type_ids)

    def get_reverse_joining_columns(self):
        return self.get_joining_columns(reverse_join=True)

    @property
    def related_fields(self):
        return [(self.through._meta.get_field_by_name('object_id')[0],
                 self.model._meta.pk)]

    @property
    def foreign_related_fields(self):
        return [self.related_fields[0][1]]


class _TaggableManager(models.Manager):
    def __init__(self, through, model, instance):
        self.through = through
        self.model = model
        self.instance = instance

    def get_query_set(self):
        return self.through.tags_for(self.model, self.instance)

    # Django 1.6 renamed this
    get_queryset = get_query_set

    def _lookup_kwargs(self):
        return self.through.lookup_kwargs(self.instance)

    @require_instance_manager
    def add(self, *tags):
        str_tags = set([
            t
            for t in tags
            if not isinstance(t, self.through.tag_model())
        ])
        tag_objs = set(tags) - str_tags
        # If str_tags has 0 elements Django actually optimizes that to not do a
        # query.  Malcolm is very smart.
        existing = self.through.tag_model().objects.filter(
            name__in=str_tags
        )
        tag_objs.update(existing)

        for new_tag in str_tags - set(t.name for t in existing):
            tag_objs.add(self.through.tag_model().objects.create(name=new_tag))

        for tag in tag_objs:
            self.through.objects.get_or_create(tag=tag, **self._lookup_kwargs())

    @require_instance_manager
    def names(self):
        return self.get_query_set().values_list('name', flat=True)

    @require_instance_manager
    def slugs(self):
        return self.get_query_set().values_list('slug', flat=True)

    @require_instance_manager
    def set(self, *tags):
        self.clear()
        self.add(*tags)

    @require_instance_manager
    def remove(self, *tags):
        self.through.objects.filter(**self._lookup_kwargs()).filter(
            tag__name__in=tags).delete()

    @require_instance_manager
    def clear(self):
        self.through.objects.filter(**self._lookup_kwargs()).delete()

    def most_common(self):
        return self.get_query_set().annotate(
            num_times=models.Count(self.through.tag_relname())
        ).order_by('-num_times')

    @require_instance_manager
    def similar_objects(self):
        lookup_kwargs = self._lookup_kwargs()
        lookup_keys = sorted(lookup_kwargs)
        qs = self.through.objects.values(*six.iterkeys(lookup_kwargs))
        qs = qs.annotate(n=models.Count('pk'))
        qs = qs.exclude(**lookup_kwargs)
        qs = qs.filter(tag__in=self.all())
        qs = qs.order_by('-n')

        # TODO: This all feels like a bit of a hack.
        items = {}
        if len(lookup_keys) == 1:
            # Can we do this without a second query by using a select_related()
            # somehow?
            f = self.through._meta.get_field_by_name(lookup_keys[0])[0]
            objs = f.rel.to._default_manager.filter(**{
                "%s__in" % f.rel.field_name: [r["content_object"] for r in qs]
            })
            for obj in objs:
                items[(getattr(obj, f.rel.field_name),)] = obj
        else:
            preload = {}
            for result in qs:
                preload.setdefault(result['content_type'], set())
                preload[result["content_type"]].add(result["object_id"])

            for ct, obj_ids in preload.items():
                ct = ContentType.objects.get_for_id(ct)
                for obj in ct.model_class()._default_manager.filter(pk__in=obj_ids):
                    items[(ct.pk, obj.pk)] = obj

        results = []
        for result in qs:
            obj = items[
                tuple(result[k] for k in lookup_keys)
            ]
            obj.similar_tags = result["n"]
            results.append(obj)
        return results


def _get_subclasses(model):
    subclasses = [model]
    for f in model._meta.get_all_field_names():
        field = model._meta.get_field_by_name(f)[0]
        if (isinstance(field, RelatedObject) and
            getattr(field.field.rel, "parent_link", None)):
            subclasses.extend(_get_subclasses(field.model))
    return subclasses


# `total_ordering` does not exist in Django 1.4, as such
# we special case this import to be py3k specific which
# is not supported by Django 1.4
if six.PY3:
    from django.utils.functional import total_ordering
    TaggableManager = total_ordering(TaggableManager)
