#!/usr/bin/env python

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
@click.option('--event-type', help='Specific value for Event header, defaults to "issues" for GitHub and "Push Hook" for GitLab')
@click.option('--verbose', is_flag=True, help='Dump HTTP communication for debugging')
@click.option('--insecure', is_flag=True, help='Ignore SSL certs if true')
def post_webhook(file, webhook_key, url, verbose, event_type, insecure):
    """
    Helper command for submitting POST requests to Webhook endpoints.

    We have two sample webhooks in tools/scripts/webhook_examples for gitlab and github.
    These or any other file can be pointed to with the --file parameter.

    \b
    Additional example webhook events can be found online.
        For GitLab see:
        https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html

    \b
        For GitHub see:
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads

    \b
    For setting up webhooks in AWX see:
        https://docs.ansible.com/ansible-tower/latest/html/userguide/webhooks.html

    \b
    Example usage for GitHub:
      ./post_webhook.py \\
        --file webhook_examples/github_push.json \\
        --url https://tower.jowestco.net:8043/api/v2/job_templates/637/github/ \\
        --key AvqBR19JDFaLTsbF3p7FmiU9WpuHsJKdHDfTqKXyzv1HtwDGZ8 \\
        --insecure \\
        --type github
    
    \b
    Example usage for GitLab:
      ./post_webhook.py \\
        --file webhook_examples/gitlab_push.json \\
        --url https://tower.jowestco.net:8043/api/v2/job_templates/638/gitlab/ \\
        --key fZ8vUpfHfb1Dn7zHtyaAsyZC5IHFcZf2a2xiBc2jmrBDptCOL2 \\
        --insecure \\
        --type=gitlab 

    \b
    NOTE: GitLab webhooks are stored in the DB with a UID of the hash of the POST body.
          After submitting one post GitLab post body a second POST of the same payload 
          can result in a response like: 
              Response code: 202
              Response body:
              {
                  "message": "Webhook previously received, aborting."
              }

          If you need to test multiple GitLab posts simply change your payload slightly

    """
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

    if url.endswith('/github/'):
        headers.update(
            {
                'X-Hub-Signature': 'sha1={}'.format(mac.hexdigest()),
                'X-GitHub-Event': 'issues' if event_type == 'default' else event_type,
                'X-GitHub-Delivery': str(uuid.uuid4()),
            }
        )
    elif url.endswith('/gitlab/'):
        mac = hmac.new(key_bytes, msg=data_bytes, digestmod=sha1)
        headers.update(
            {
                'X-GitLab-Event': 'Push Hook' if event_type == 'default' else event_type,
                'X-GitLab-Token': webhook_key,
            }
        )
    else:
        click.echo("This utility only knows how to support URLs that end in /github/ or /gitlab/.")
        exit(250)

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
