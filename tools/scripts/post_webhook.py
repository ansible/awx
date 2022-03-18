#!/usr/bin/env python

# You can lookup sample webhook events online.
#    GitLab - https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html
#    GitHub - https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads
#

# User modified variables (maybe params?)
# file = 'webhook_payload.json'
# webhook_key = 'AvqBR19JDFaLTsbF3p7FmiU9WpuHsJKdHDfTqKXyzv1HtwDGZ8'
# url = 'https://tower.jowestco.net:8043/api/v2/job_templates/637/github/'
# verbose = False
# webhook_type = 'git'
# event_type =

from hashlib import sha1
from sys import exit
import click
import hmac
import http.client as http_client
import json
import logging
import requests
import urllib3
import uuid


@click.command()
@click.option('--file', required=True, help='File containing the post data.')
@click.option('--key', "webhook_key", required=True, help='The webhook key for the job template.')
@click.option('--url', required=True, help='The webhook url for the job template (i.e. https://tower.jowestco.net:8043/api/v2/job_templates/637/github/.')
@click.option(
    '--type', "webhook_type", default='git', type=click.Choice(['git', 'gitlab']), help='What type of webhook is being sent (will send appropriate headers)'
)
@click.option('--event-type', help='Specific value for Event header, defaults to "issues" for GitHub and "Push Hook" for GitLab')
@click.option('--verbose', is_flag=True, help='Dump HTTP communication for debugging')
@click.option('--insecure', is_flag=True, help='Ignore SSL certs if true')
def post_webhook(file, webhook_key, url, verbose, webhook_type, event_type, insecure):

    if insecure:
        # Disable insecure warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if verbose:
        # Enable HTTP debugging
        http_client.HTTPConnection.debuglevel = 1
        # Configure logging
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    # read webhook payload
    with open(file, 'r') as f:
        post_data = json.loads(f.read())

    # Construct Headers
    headers = {
        'Content-Type': 'application/json',
    }

    # Encode key and post_data
    key_bytes = webhook_key.encode('utf-8', 'strict')
    data_bytes = str(json.dumps(post_data)).encode('utf-8', 'strict')

    # Compute sha1 mac
    mac = hmac.new(key_bytes, msg=data_bytes, digestmod=sha1)

    if webhook_type == 'git':
        headers.update(
            {
                'X-Hub-Signature': 'sha1={}'.format(mac.hexdigest()),
                'X-GitHub-Event': 'issues' if event_type == 'default' else event_type,
                'X-GitHub-Delivery': str(uuid.uuid4()),
            }
        )
    elif webhook_type == 'gitlab':
        mac = hmac.new(key_bytes, msg=data_bytes, digestmod=sha1)
        headers.update(
            {
                'X-GitLab-Event': 'Push Hook' if event_type == 'default' else event_type,
                'X-GitLab-Token': webhook_key,
            }
        )

    # Make post
    r = requests.post(url, data=json.dumps(post_data), headers=headers, verify=(not insecure))

    if not verbose:
        click.echo("Response code: {}".format(r.status_code))
        click.echo("Response body:")
    try:
        click.echo(json.dumps(r.json(), indent=4))
    except:
        click.echo(r.text)


if __name__ == '__main__':
    post_webhook()
