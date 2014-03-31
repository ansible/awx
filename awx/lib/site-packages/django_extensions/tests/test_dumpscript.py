import sys
import six

if sys.version_info[:2] >= (2, 6):
    import ast as compiler  # NOQA
else:
    import compiler  # NOQA

from django.core.management import call_command

from django_extensions.tests.models import Name, Note, Person
from django_extensions.tests.fields import FieldTestCase


class DumpScriptTests(FieldTestCase):
    def setUp(self):
        super(DumpScriptTests, self).setUp()

        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        sys.stdout = six.StringIO()
        sys.stderr = six.StringIO()

    def tearDown(self):
        super(DumpScriptTests, self).tearDown()

        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr

    def test_runs(self):
        # lame test...does it run?
        n = Name(name='Gabriel')
        n.save()
        call_command('dumpscript', 'tests')
        self.assertTrue('Gabriel' in sys.stdout.getvalue())

    #----------------------------------------------------------------------
    def test_replaced_stdout(self):
        # check if stdout can be replaced
        sys.stdout = six.StringIO()
        n = Name(name='Mike')
        n.save()
        tmp_out = six.StringIO()
        call_command('dumpscript', 'tests', stdout=tmp_out)
        self.assertTrue('Mike' in tmp_out.getvalue())  # script should go to tmp_out
        self.assertEqual(0, len(sys.stdout.getvalue()))  # there should not be any output to sys.stdout
        tmp_out.close()

    #----------------------------------------------------------------------
    def test_replaced_stderr(self):
        # check if stderr can be replaced, without changing stdout
        n = Name(name='Fred')
        n.save()
        tmp_err = six.StringIO()
        sys.stderr = six.StringIO()
        call_command('dumpscript', 'tests', stderr=tmp_err)
        self.assertTrue('Fred' in sys.stdout.getvalue())  # script should still go to stdout
        self.assertTrue('Name' in tmp_err.getvalue())  # error output should go to tmp_err
        self.assertEqual(0, len(sys.stderr.getvalue()))  # there should not be any output to sys.stderr
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
        tmp_out = six.StringIO()
        call_command('dumpscript', 'tests', stdout=tmp_out)
        ast_syntax_tree = compiler.parse(tmp_out.getvalue())
        if hasattr(ast_syntax_tree, 'body'):
            self.assertTrue(len(ast_syntax_tree.body) > 1)
        else:
            self.assertTrue(len(ast_syntax_tree.asList()) > 1)
        tmp_out.close()

