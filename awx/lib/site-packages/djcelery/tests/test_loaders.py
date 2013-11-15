from __future__ import absolute_import, unicode_literals

from celery import loaders

from djcelery import loaders as djloaders
from djcelery.app import app
from djcelery.tests.utils import unittest


class TestDjangoLoader(unittest.TestCase):

    def setUp(self):
        self.loader = djloaders.DjangoLoader(app=app)

    def test_get_loader_cls(self):

        self.assertEqual(loaders.get_loader_cls('django'),
                         self.loader.__class__)
        # Execute cached branch.
        self.assertEqual(loaders.get_loader_cls('django'),
                         self.loader.__class__)

    def test_on_worker_init(self):
        from django.conf import settings
        old_imports = getattr(settings, 'CELERY_IMPORTS', ())
        settings.CELERY_IMPORTS = ('xxx.does.not.exist', )
        try:
            self.assertRaises(ImportError, self.loader.import_default_modules)
        finally:
            settings.CELERY_IMPORTS = old_imports

    def test_race_protection(self):
        djloaders._RACE_PROTECTION = True
        try:
            self.assertFalse(self.loader.on_worker_init())
        finally:
            djloaders._RACE_PROTECTION = False

    def test_find_related_module_no_path(self):
        self.assertFalse(djloaders.find_related_module('sys', 'tasks'))

    def test_find_related_module_no_related(self):
        self.assertFalse(
            djloaders.find_related_module('someapp', 'frobulators'),
        )
