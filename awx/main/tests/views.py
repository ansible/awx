# Django
from django.core.urlresolvers import reverse

# Reuse Test code
from awx.main.tests.base import BaseLiveServerTest, QueueStartStopTestMixin
from awx.main.tests.base import URI

__all__ = ['UnifiedJobStdoutTests']


TEST_STDOUTS = []
uri = URI(scheme="https", username="Dhh3U47nmC26xk9PKscV", password="PXPfWW8YzYrgS@E5NbQ2H@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append({
    'uri' : uri,
    'text' : 'hello world %s goodbye world' % uri,
    'host_occurrences' : 1
})

uri = URI(scheme="https", username="applepie@@@", password="thatyouknow@@@@", host="github.ginger.com/theirrepo.git/info/refs")
TEST_STDOUTS.append({
    'uri' : uri,
    'text' : 'hello world %s \n\nyoyo\n\nhello\n%s' % (uri, uri),
    'host_occurrences' : 2
})


class UnifiedJobStdoutTests(BaseLiveServerTest, QueueStartStopTestMixin):

    def setUp(self):
        super(UnifiedJobStdoutTests, self).setUp()
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
    def test_redaction_enabled(self):
        for test_data in self.test_cases:
            uri = test_data['uri']
            job_stdout_url = reverse('api:job_stdout', args=(test_data['job'].pk,))

            response = self.get(job_stdout_url, expect=200, auth=self.get_super_credentials(), accept='application/json')

            self.assertIsNotNone(response['content'])
            self.check_not_found(response['content'], uri.username)
            self.check_not_found(response['content'], uri.password)
            # Ensure the host didn't get redacted
            self.check_found(response['content'], uri.host, count=test_data['host_occurrences'])
