import sys

# conditional imports for python 3
try:
    import compiler  # NOQA
    from StringIO import StringIO  # NOQA
except ImportError:
    import ast as compiler  # NOQA
    from io import StringIO  # NOQA
from django.test import TestCase

from django.core.management import call_command
from django_extensions.tests.models import Name, Note, Person

from django.conf import settings
from django.db.models import loading


class DumpScriptTests(TestCase):
    def setUp(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        self.original_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('django_extensions.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr
        settings.INSTALLED_APPS.remove('django_extensions.tests')
        settings.INSTALLED_APPS = self.original_installed_apps
        loading.cache.loaded = False

    def test_runs(self):
        # lame test...does it run?
        n = Name(name='Gabriel')
        n.save()
        call_command('dumpscript', 'tests')
        self.assertTrue('Gabriel' in sys.stdout.getvalue())

    #----------------------------------------------------------------------
    def test_replaced_stdout(self):
        # check if stdout can be replaced
        sys.stdout = StringIO()
        n = Name(name='Mike')
        n.save()
        tmp_out = StringIO()
        call_command('dumpscript', 'tests', stdout=tmp_out)
        self.assertTrue('Mike' in tmp_out.getvalue())  # script should go to tmp_out
        self.assertEquals(0, len(sys.stdout.getvalue()))  # there should not be any output to sys.stdout
        tmp_out.close()

    #----------------------------------------------------------------------
    def test_replaced_stderr(self):
        # check if stderr can be replaced, without changing stdout
        n = Name(name='Fred')
        n.save()
        tmp_err = StringIO()
        sys.stderr = StringIO()
        call_command('dumpscript', 'tests', stderr=tmp_err)
        self.assertTrue('Fred' in sys.stdout.getvalue())  # script should still go to stdout
        self.assertTrue('Name' in tmp_err.getvalue())  # error output should go to tmp_err
        self.assertEquals(0, len(sys.stderr.getvalue()))  # there should not be any output to sys.stderr
        tmp_err.close()

    #----------------------------------------------------------------------
    def test_valid_syntax(self):
        n1 = Name(name='John')
        n1.save()
        p1 = Person(name=n1, age=40)
        p1.save()
        n2 = Name(name='Jane')
        n2.save()
        p2 = Person(name=n2, age=18)
        p2.save()
        p2.children.add(p1)
        note1 = Note(note="This is the first note.")
        note1.save()
        note2 = Note(note="This is the second note.")
        note2.save()
        p2.notes.add(note1, note2)
        tmp_out = StringIO()
        call_command('dumpscript', 'tests', stdout=tmp_out)
        ast_syntax_tree = compiler.parse(tmp_out.getvalue())
        if hasattr(ast_syntax_tree, 'body'):
            self.assertTrue(len(ast_syntax_tree.body) > 1)
        else:
            self.assertTrue(len(ast_syntax_tree.asList()) > 1)
        tmp_out.close()

