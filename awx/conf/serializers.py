# Django REST Framework
from rest_framework import serializers

# Tower
from awx.api.fields import VerbatimField
from awx.api.serializers import BaseSerializer
from awx.conf.models import Setting
from awx.conf import settings_registry


class SettingSerializer(BaseSerializer):
    """Read-only serializer for activity stream."""

    value = VerbatimField(allow_null=True)

    class Meta:
        model = Setting
        fields = ('id', 'key', 'value')
        read_only_fields = ('id', 'key', 'value')

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        if instance is None and data is not serializers.empty and 'key' in data:
            try:
                instance = Setting.objects.get(key=data['key'])
            except Setting.DoesNotExist:
                pass
        super(SettingSerializer, self).__init__(instance, data, **kwargs)


class SettingCategorySerializer(serializers.Serializer):
    """Serialize setting category """

    url = serializers.CharField(
        read_only=True,
    )
    slug = serializers.CharField(
        read_only=True,
    )
    name = serializers.CharField(
        read_only=True,
    )


class SettingFieldMixin(object):
    """Mixin to use a registered setting field class for API display/validation."""

    def to_representation(self, obj):
        if getattr(self, 'encrypted', False) and isinstance(obj, str) and obj:
            return '$encrypted$'
        return obj

    def to_internal_value(self, value):
        if getattr(self, 'encrypted', False) and isinstance(value, str) and value.startswith('$encrypted$'):
            raise serializers.SkipField()
        obj = super(SettingFieldMixin, self).to_internal_value(value)
        return super(SettingFieldMixin, self).to_representation(obj)


class SettingSingletonSerializer(serializers.Serializer):
    """Present a group of settings (by category) as a single object."""

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        # Instance (if given) should be an object with attributes for all of the
        # settings in the category; never an actual Setting model instance.
        assert instance is None or not hasattr(instance, 'pk')
        super(SettingSingletonSerializer, self).__init__(instance, data, **kwargs)

    def validate(self, attrs):
        try:
            category_slug = self.context['view'].kwargs.get('category_slug', 'all')
        except (KeyError, AttributeError):
            category_slug = ''
        if self.context['view'].kwargs.get('category_slug', '') == 'all':
            for validate_func in settings_registry._validate_registry.values():
                attrs = validate_func(self, attrs)
            return attrs
        custom_validate = settings_registry.get_registered_validate_func(category_slug)
        return custom_validate(self, attrs) if custom_validate else attrs

    def get_fields(self):
        fields = super(SettingSingletonSerializer, self).get_fields()
        try:
            category_slug = self.context['view'].kwargs.get('category_slug', 'all')
        except (KeyError, AttributeError):
            category_slug = ''
        for key in settings_registry.get_registered_settings(category_slug=category_slug):
            if self.instance and not hasattr(self.instance, key):
                continue
            extra_kwargs = {}
            # Make LICENSE and AWX_ISOLATED_KEY_GENERATION read-only here;
            # LICENSE is only updated via /api/v2/config/
            # AWX_ISOLATED_KEY_GENERATION is only set/unset via the setup playbook
            if key in ('LICENSE', 'AWX_ISOLATED_KEY_GENERATION'):
                extra_kwargs['read_only'] = True
            field = settings_registry.get_setting_field(key, mixin_class=SettingFieldMixin, for_user=bool(category_slug == 'user'), **extra_kwargs)
            fields[key] = field
        return fields
