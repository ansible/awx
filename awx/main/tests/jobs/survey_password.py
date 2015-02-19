# Python
import json

# Django
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import * # noqa
from awx.main.tests.base import BaseTest

__all__ = ['SurveyPasswordRedactedTest']

PASSWORD="5m/h"
ENCRYPTED_STR='$encrypted$'

TEST_PLAYBOOK = u'''---
- name: test success
  hosts: test-group
  gather_facts: True
  tasks:
  - name: should pass
    command: echo {{ %s }}
''' % ('spot_speed')


TEST_SIMPLE_SURVEY = '''
{
    "name": "Simple",
    "description": "Description",
    "spec": [
        {
        "type": "password",
        "question_name": "spots speed",
        "question_description": "How fast can spot run?",
        "variable": "%s",
        "choices": "",
        "min": "",
        "max": "",
        "required": false,
        "default": "%s"
        }
    ]
}
''' % ('spot_speed', PASSWORD)

TEST_COMPLEX_SURVEY = '''
{
    "name": "Simple",
    "description": "Description",
    "spec": [
        {
        "type": "password",
        "question_name": "spots speed",
        "question_description": "How fast can spot run?",
        "variable": "spot_speed",
        "choices": "",
        "min": "",
        "max": "",
        "required": false,
        "default": "0m/h"
        },
        {
        "type": "password",
        "question_name": "ssn",
        "question_description": "What's your social security number?",
        "variable": "ssn",
        "choices": "",
        "min": "",
        "max": "",
        "required": false,
        "default": "999-99-9999"
        },
        {
        "type": "password",
        "question_name": "bday",
        "question_description": "What's your birth day?",
        "variable": "bday",
        "choices": "",
        "min": "",
        "max": "",
        "required": false,
        "default": "1/1/1970"
        }
    ]
}
'''


TEST_SINGLE_PASSWORDS = [
    { 
        'description': 'Single instance with a . after',
        'text' : 'See spot. See spot run. See spot run %s. That is a fast run.' % PASSWORD,
        'passwords': [PASSWORD],
        'occurances': 1,
    },
    {
        'description': 'Single instance with , after',
        'text': 'Spot goes %s, at a fast pace' % PASSWORD,
        'passwords': [PASSWORD],
        'occurances': 1,
    },
    {
        'description': 'Single instance with a space after',
        'text': 'Is %s very fast?' % PASSWORD,
        'passwords': [PASSWORD],
        'occurances': 1,
    },
    {
        'description': 'Many instances, also with newline',
        'text': 'I think %s is very very fast. If I ran %s for 4 hours how many hours would I run?.\nTrick question. %s for 4 hours would result in running for 4 hours' % (PASSWORD, PASSWORD, PASSWORD),
        'passwords': [PASSWORD],
        'occurances': 3,
    },
]
passwd = 'my!@#$%^pass&*()_+'
TEST_SINGLE_PASSWORDS.append({
    'description': 'password includes characters not in a-z 0-9 range',
    'passwords': [passwd],
    'text': 'Text is fun yeah with passwords %s.' % passwd,
    'occurances': 1
})

# 3 because 3 password fields in spec TEST_COMPLEX_SURVEY
TEST_MULTIPLE_PASSWORDS = []
passwds = [ '65km/s', '545-83-4534', '7/4/2002']
TEST_MULTIPLE_PASSWORDS.append({
    'description': '3 different passwords each used once',
    'text': 'Spot runs %s. John has an ss of %s and is born on %s.' % (passwds[0], passwds[1], passwds[2]),
    'passwords': passwds,
    'occurances': 3,
})

TESTS = {
    'simple': {
        'survey' : json.loads(TEST_SIMPLE_SURVEY),
        'tests' : TEST_SINGLE_PASSWORDS,
    },
    'complex': {
        'survey' : json.loads(TEST_COMPLEX_SURVEY),
        'tests' : TEST_MULTIPLE_PASSWORDS,
    }
}

class SurveyPasswordBaseTest(BaseTest):
    def setUp(self):
        super(SurveyPasswordBaseTest, self).setUp()
        self.setup_instances()
        self.setup_users()

    def check_passwords_redacted(self, test, response):
        self.assertIsNotNone(response['content'])
        for password in test['passwords']:
            self.check_not_found(response['content'], password, test['description'], word_boundary=True)

        self.check_found(response['content'], ENCRYPTED_STR, test['occurances'], test['description'])

    # TODO: A more complete test would ensure that the variable value isn't found
    def check_extra_vars_redacted(self, test, response):
        self.assertIsNotNone(response)
        # Ensure that all extra_vars of type password have the value '$encrypted$'
        vars = []
        for question in test['survey']['spec']:
            if question['type'] == 'password':
                vars.append(question['variable'])

        extra_vars = json.loads(response['extra_vars'])
        for var in vars:
            self.assertIn(var, extra_vars, 'Variable "%s" should exist in "%s"' % (var, extra_vars))
            self.assertEqual(extra_vars[var], ENCRYPTED_STR)

    def _get_url_job_stdout(self, job):
        url = reverse('api:job_stdout', args=(job.pk,))
        return self.get(url, expect=200, auth=self.get_super_credentials(), accept='application/json')

    def _get_url_job_details(self, job):
        url = reverse('api:job_detail', args=(job.pk,))
        return self.get(url, expect=200, auth=self.get_super_credentials(), accept='application/json')

class SurveyPasswordRedactedTest(SurveyPasswordBaseTest):
    '''
    Transpose TEST[]['tests'] to the below format. A more flat format."
    [
      {
        'text': '...',
        'description': '...',
        ...,
        'job': '...',
        'survey': '...'
      },
    ]
    '''
    def setup_test(self, test_name):
        blueprint = TESTS[test_name]
        self.tests[test_name] = []

        job_template = self.make_job_template(survey_enabled=True, survey_spec=blueprint['survey'])
        for test in blueprint['tests']:
            test = dict(test)
            extra_vars = {}

            # build extra_vars from spec variables and passwords
            for x in range(0, len(blueprint['survey']['spec'])):
                question = blueprint['survey']['spec'][x]
                extra_vars[question['variable']] = test['passwords'][x]

            job = self.make_job(job_template=job_template)
            job.extra_vars = json.dumps(extra_vars)
            job.result_stdout_text = test['text']
            job.save()
            test['job'] = job
            test['survey'] = blueprint['survey']
            self.tests[test_name].append(test)

    def setUp(self):
        super(SurveyPasswordRedactedTest, self).setUp()

        self.tests = {}
        self.setup_test('simple')
        self.setup_test('complex')

    # should redact single variable survey
    def test_redact_stdout_simple_survey(self):
        for test in self.tests['simple']:
            response = self._get_url_job_stdout(test['job'])
            self.check_passwords_redacted(test, response)

    # should redact multiple variables survey
    def test_redact_stdout_complex_survey(self):
        for test in self.tests['complex']:
            response = self._get_url_job_stdout(test['job'])
            self.check_passwords_redacted(test, response)

    # should redact values in extra_vars
    def test_redact_job_extra_vars(self):
        for test in self.tests['simple']:
            response = self._get_url_job_details(test['job']) 
            self.check_extra_vars_redacted(test, response)
