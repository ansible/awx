ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'tower'}


DOCUMENTATION = '''
---
module: insights
short_description: gather all maintenance plan playbooks for an insights account
description:
  - Supply insights Credentials to download all playbooks for all maintenance plans.
    The totality of the plans are versioned based on the http ETag response.
version_added: "2.3"
options:
  insights_url:
    description:
    - The base url of the insights api. Most likely https://insights.redhat.com
    required: true
  username:
    description:
    - Insights basic auth username.
    required: true
  password:
    description:
    - Insights basic auth password.
    required: true
  project_path:
    description:
    - Directory to write all playbooks and the special .version to.
    required: true

notes:
    - Returns version
author:
    - "Chris Meyers"
'''

EXAMPLES = '''
- insights:
    insights_url: "https://insights.redhat.com"
    username: "cmoney"
    password: "get_paid"
    project_path: "/var/lib/awx/projects/_5_insights"
'''
