from django.db import models  # NOQA
from django_extensions.tests.test_dumpscript import DumpScriptTests
from django_extensions.tests.utils import TruncateLetterTests
from django_extensions.tests.json_field import JsonFieldTest
from django_extensions.tests.uuid_field import UUIDFieldTest
from django_extensions.tests.fields import AutoSlugFieldTest
from django_extensions.tests.management_command import CommandTest, ShowTemplateTagsTests


__test_classes__ = [
    DumpScriptTests, JsonFieldTest, UUIDFieldTest, AutoSlugFieldTest, CommandTest,
    ShowTemplateTagsTests, TruncateLetterTests
]

try:
    from django_extensions.tests.encrypted_fields import EncryptedFieldsTestCase
    __test_classes__.append(EncryptedFieldsTestCase)
except ImportError:
    pass
