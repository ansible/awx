# Django
from django.core.urlresolvers import reverse

# Reuse Test code
from awx.main.tests.base import BaseLiveServerTest, QueueStartStopTestMixin
from awx.main.tests.base import URI
from awx.main.models.projects import * # noqa

__all__ = ['UnifiedJobStdoutRedactedTests']


TEST_STDOUTS = []
uri = URI(scheme="https", username="Dhh3U47nmC26xk9PKscV", password="PXPfWW8YzYrgS@E5NbQ2H@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append({
    'description': 'uri in a plain text document',
    'uri' : uri,
    'text' : 'hello world %s goodbye world' % uri,
    'occurrences' : 1
})

uri = URI(scheme="https", username="applepie@@@", password="thatyouknow@@@@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append({
    'description': 'uri appears twice in a multiline plain text document',
    'uri' : uri,
    'text' : 'hello world %s \n\nyoyo\n\nhello\n%s' % (uri, uri),
    'occurrences' : 2
})

class UnifiedJobStdoutRedactedTests(BaseLiveServerTest, QueueStartStopTestMixin):

    def setUp(self):
        super(UnifiedJobStdoutRedactedTests, self).setUp()
        self.setup_instances()
        self.setup_users()        
        self.test_cases = []
        self.negative_test_cases = []

        proj = self.make_project()

        for e in TEST_STDOUTS:
            e['project'] = ProjectUpdate(project=proj)
            e['project'].result_stdout_text = e['text']
            e['project'].save()
            self.test_cases.append(e)
        for d in TEST_STDOUTS:
            d['job'] = self.make_job()
            d['job'].result_stdout_text = d['text']
            d['job'].save()
            self.negative_test_cases.append(d)

    # This is more of a functional test than a unit test.
    # should filter out username and password
    def check_sensitive_redacted(self, test_data, response):
        uri = test_data['uri']
        self.assertIsNotNone(response['content'])
        self.check_not_found(response['content'], uri.username, test_data['description'])
        self.check_not_found(response['content'], uri.password, test_data['description'])
        # Ensure the host didn't get redacted
        self.check_found(response['content'], uri.host, test_data['occurrences'], test_data['description'])

    def check_sensitive_not_redacted(self, test_data, response):
        uri = test_data['uri']
        self.assertIsNotNone(response['content'])
        self.check_found(response['content'], uri.username, description=test_data['description'])
        self.check_found(response['content'], uri.password, description=test_data['description'])

    def _get_url_job_stdout(self, job, url_base, format='json'):
        formats = {
            'json': 'application/json',
            'ansi': 'text/plain',
            'txt': 'text/plain',
            'html': 'text/html',
        }
        content_type = formats[format]
        project_update_stdout_url = reverse(url_base, args=(job.pk,)) + "?format=" + format
        return self.get(project_update_stdout_url, expect=200, auth=self.get_super_credentials(), accept=content_type)

    def _test_redaction_enabled(self, format):
        for test_data in self.test_cases:
            response = self._get_url_job_stdout(test_data['project'], "api:project_update_stdout", format=format)
            self.check_sensitive_redacted(test_data, response)

    def _test_redaction_disabled(self, format):
        for test_data in self.negative_test_cases:
            response = self._get_url_job_stdout(test_data['job'], "api:job_stdout", format=format)
            self.check_sensitive_not_redacted(test_data, response)

    def test_project_update_redaction_enabled_json(self):
        self._test_redaction_enabled('json')

    def test_project_update_redaction_enabled_ansi(self):
        self._test_redaction_enabled('ansi')

    def test_project_update_redaction_enabled_html(self):
        self._test_redaction_enabled('html')

    def test_project_update_redaction_enabled_txt(self):
        self._test_redaction_enabled('txt')

    def test_job_redaction_disabled_json(self):
        self._test_redaction_disabled('json')

    def test_job_redaction_disabled_ansi(self):
        self._test_redaction_disabled('ansi')

    def test_job_redaction_disabled_html(self):
        self._test_redaction_disabled('html')

    def test_job_redaction_disabled_txt(self):
        self._test_redaction_disabled('txt')
