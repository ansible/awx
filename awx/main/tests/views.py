# Django
from django.core.urlresolvers import reverse

# Reuse Test code
from awx.main.tests.base import BaseLiveServerTest, QueueStartStopTestMixin
from awx.main.tests.base import URI

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

        for e in TEST_STDOUTS:
            e['job'] = self.make_job()
            e['job'].result_stdout_text = e['text']
            e['job'].save()
            self.test_cases.append(e)

    # This is more of a functional test than a unit test.
    # should filter out username and password
    def check_sensitive_redacted(self, test_data, response):
        uri = test_data['uri']
        self.assertIsNotNone(response['content'])
        self.check_not_found(response['content'], uri.username, test_data['description'])
        self.check_not_found(response['content'], uri.password, test_data['description'])
        # Ensure the host didn't get redacted
        self.check_found(response['content'], uri.host, test_data['occurrences'], test_data['description'])

    def _get_url_job_stdout(self, job, format='json'):
        formats = {
            'json': 'application/json',
            'ansi': 'text/plain',
            'txt': 'text/plain',
            'html': 'text/html',
        }
        content_type = formats[format]
        job_stdout_url = reverse('api:job_stdout', args=(job.pk,)) + "?format=" + format
        return self.get(job_stdout_url, expect=200, auth=self.get_super_credentials(), accept=content_type)

    def _test_redaction_enabled(self, format):
        for test_data in self.test_cases:
            response = self._get_url_job_stdout(test_data['job'], format=format)
            self.check_sensitive_redacted(test_data, response)

    def test_redaction_enabled_json(self):
        self._test_redaction_enabled('json')

    def test_redaction_enabled_ansi(self):
        self._test_redaction_enabled('ansi')

    def test_redaction_enabled_html(self):
        self._test_redaction_enabled('html')

    def test_redaction_enabled_txt(self):
        self._test_redaction_enabled('txt')