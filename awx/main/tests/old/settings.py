# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from awx.main.tests.base import BaseTest
from awx.main.models import * # noqa

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

TEST_TOWER_SETTINGS_MANIFEST = {
    "TEST_SETTING_INT": {
        "name": "An Integer Field",
        "description": "An Integer Field",
        "default": 1,
        "type": "int",
        "category": "test"
    },
    "TEST_SETTING_STRING": {
        "name": "A String Field",
        "description": "A String Field",
        "default": "test",
        "type": "string",
        "category": "test"
    },
    "TEST_SETTING_BOOL": {
        "name": "A Bool Field",
        "description": "A Bool Field",
        "default": True,
        "type": "bool",
        "category": "test"
    },
    "TEST_SETTING_LIST": {
        "name": "A List Field",
        "description": "A List Field",
        "default": ["A", "Simple", "List"],
        "type": "list",
        "category": "test"
    }
}

@override_settings(TOWER_SETTINGS_MANIFEST=TEST_TOWER_SETTINGS_MANIFEST)
class SettingsTest(BaseTest):

    def setUp(self):
        super(SettingsTest, self).setUp()
        self.setup_instances()
        self.setup_users()

    def get_settings(self, expected_count=4):
        result = self.get(reverse('api:settings_list'), expect=200)
        self.assertEqual(result['count'], expected_count)
        return result['results']

    def get_individual_setting(self, setting):
        all_settings = self.get_settings()
        setting_actual = None
        for setting_item in all_settings:
            if setting_item['key'] == setting:
                setting_actual = setting_item
                break
        self.assertIsNotNone(setting_actual)
        return setting_actual

    def set_setting(self, key, value):
        self.post(reverse('api:settings_list'), data={"key": key, "value": value}, expect=201)

    def test_get_settings(self):
        # Regular user should see nothing (no user settings yet)
        with self.current_user(self.normal_django_user):
            self.get_settings(expected_count=0)
        # anonymous user should get a 401
        self.get(reverse('api:settings_list'), expect=401)
        # super user can see everything
        with self.current_user(self.super_django_user):
            self.get_settings(expected_count=len(TEST_TOWER_SETTINGS_MANIFEST))

    def test_set_and_reset_settings(self):
        settings_reset = reverse('api:settings_reset')
        with self.current_user(self.super_django_user):
            # Set and reset a single setting
            setting_int = self.get_individual_setting('TEST_SETTING_INT')
            self.assertEqual(setting_int['value'], TEST_TOWER_SETTINGS_MANIFEST['TEST_SETTING_INT']['default'])
            self.set_setting('TEST_SETTING_INT', 2)
            setting_int = self.get_individual_setting('TEST_SETTING_INT')
            self.assertEqual(setting_int['value'], 2)
            self.set_setting('TEST_SETTING_INT', 3)
            setting_int = self.get_individual_setting('TEST_SETTING_INT')
            self.assertEqual(setting_int['value'], 3)
            self.post(settings_reset, data={"key": 'TEST_SETTING_INT'}, expect=204)
            setting_int = self.get_individual_setting('TEST_SETTING_INT')
            self.assertEqual(setting_int['value'], TEST_TOWER_SETTINGS_MANIFEST['TEST_SETTING_INT']['default'])

    def test_clear_all_settings(self):
        settings_list = reverse('api:settings_list')
        with self.current_user(self.super_django_user):
            self.set_setting('TEST_SETTING_INT', 2)
            self.set_setting('TEST_SETTING_STRING', "foo")
            self.set_setting('TEST_SETTING_BOOL', False)
            self.set_setting('TEST_SETTING_LIST', [1,2,3])
            all_settings = self.get_settings()
            for setting_entry in all_settings:
                self.assertNotEqual(setting_entry['value'],
                                    TEST_TOWER_SETTINGS_MANIFEST[setting_entry['key']]['default'])
            self.delete(settings_list, expect=200)
            all_settings = self.get_settings()
            for setting_entry in all_settings:
                self.assertEqual(setting_entry['value'],
                                 TEST_TOWER_SETTINGS_MANIFEST[setting_entry['key']]['default'])
