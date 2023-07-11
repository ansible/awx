#!/usr/bin/env python

missing_modules = []
try:
    import requests
except:
    missing_modules.append('requests')
import json
import os
import re
import sys
import time

try:
    import semantic_version
except:
    missing_modules.append('semantic_version')

if len(missing_modules) > 0:
    print("This requires python libraries to work; try:")
    for a_module in missing_modules:
        print("    pip install {}".format(a_module))
    sys.exit(1)


def getCurrentVersions():
    print("Getting current versions")
    for repo in product_repos:
        response = session.get('https://api.github.com/repos/ansible/{}/releases'.format(repo))
        if 'X-RateLimit-Limit' in response.headers and int(response.headers['X-RateLimit-Limit']) <= 60:
            print("Your key in .github_creds did not work right and you are using unauthenticated requests")
            print("This script would likely overrun your available requests, exiting")
            sys.exit(3)
        versions['current'][repo] = response.json()[0]['tag_name']
        print("    {}: {}".format(repo, versions['current'][repo]))


def getNextReleases():
    #
    # This loads the commits since the last release and gets their associated PRs and scans those for release_type: [xyz]
    # Any X or Y changes also get captured for bullhorn release notes
    #
    for repo in product_repos:
        response = session.get('https://api.github.com/repos/ansible/{}/compare/{}...devel'.format(repo, versions['current'][repo]))
        commit_data = response.json()
        pr_votes = {}
        suggested_release_type = None
        prs_missing_relese_type = 0
        versions['release_notes'][repo] = []
        for commit in commit_data['commits']:
            response = session.get('https://api.github.com/repos/ansible/{}/commits/{}/pulls'.format(repo, commit['sha']))
            prs = response.json()
            for a_pr in prs:
                # If we've already seen this PR we don't need to check again
                try:
                    if a_pr['html_url'] in pr_votes:
                        continue
                except:
                    print("Unable to check on PR")
                    print(json.dumps(a_pr, indent=4))
                    sys.exit(255)
                append_title = False
                pr_release = 'is non voting'
                if a_pr and a_pr.get('body', None):
                    if 'Breaking Change' in a_pr['body']:
                        suggested_release_type = 'x'
                        pr_release = 'votes x'
                        append_title = True
                    elif 'New or Enhanced Feature' in a_pr['body']:
                        if suggested_release_type != 'x':
                            suggested_release_type = 'y'
                        pr_release = 'votes y'
                        append_title = True
                    elif 'Bug, Docs Fix or other nominal change' in a_pr['body']:
                        if suggested_release_type == None:
                            suggested_release_type = 'z'
                        pr_release = 'votes z'
                    # This was a format along the way
                    elif 'Bug or Docs Fix' in a_pr['body']:
                        if suggested_release_type == None:
                            suggested_release_type = 'z'
                        pr_release = 'votes z'
                    # Old PR format
                    elif (
                        '- Bug Report' in a_pr['body']
                        or '- Bug Fix' in a_pr['body']
                        or '- Bugfix Pull Request' in a_pr['body']
                        or '- Documentation' in a_pr['body']
                        or '- Docs Pull Request' in a_pr['body']
                    ):
                        if suggested_release_type == None:
                            suggested_release_type = 'z'
                        pr_release = 'votes z (from old PR body)'
                    elif '- Feature Idea' in a_pr['body'] or '- Feature Pull Request' in a_pr['body']:
                        if suggested_release_type != 'x':
                            suggested_release_type = 'y'
                        pr_release = 'votes y (from old PR body)'
                        append_title = True
                    else:
                        prs_missing_relese_type += 1
                else:
                    prs_missing_relese_type += 1

                if append_title:
                    versions['release_notes'][repo].append("* {}".format(a_pr['title']))
                print("PR {} {}".format(a_pr['html_url'], pr_release))
                pr_votes[a_pr['html_url']] = pr_release

        print("https://github.com/ansible/{}/compare/{}...devel".format(repo, versions['current'][repo]))
        print("{} devel is {} commit(s) ahead of release {}".format(repo, commit_data['total_commits'], versions['current'][repo]))
        if prs_missing_relese_type == 0:
            print("\nAll commits voted, the release type suggestion is {}".format(suggested_release_type))
        else:
            total_prs = len(pr_votes)
            voted_prs = total_prs - prs_missing_relese_type
            print("From {} commits, {} of {} PRs voted".format(commit_data['total_commits'], voted_prs, total_prs))
            if suggested_release_type:
                print("\nOf commits with release type, the suggestion is {}".format(suggested_release_type))
            else:
                print("\nNone of the commits had the release type indicated")
        print()

        current_version = semantic_version.Version(versions['current'][repo])
        if suggested_release_type.lower() == 'x':
            versions['next'][repo] = current_version.next_major()
        elif suggested_release_type.lower() == 'y':
            versions['next'][repo] = current_version.next_minor()
        else:
            versions['next'][repo] = current_version.next_patch()


#
# Load the users session information
#
session = requests.Session()
try:
    print("Loading credentials")
    with open(".github_creds", "r") as f:
        password = f.read().strip()
    session.headers.update({'Authorization': 'bearer {}'.format(password), 'Accept': 'application/vnd.github.v3+json'})
except Exception:
    print("Failed to load credentials from ./.github_creds")
    sys.exit(255)

versions = {
    'current': {},
    'next': {},
    'release_notes': {},
}

product_repos = ['awx', 'awx-operator']

#
# Get latest release version from releases page
#
getCurrentVersions()

#
# Scan PRs for release types
#
getNextReleases()

#
# Confirm the release number with the human
#
print(
    '''

Next recommended releases:
  AWX: {0}
  Operator: {1}

'''.format(
        versions['next']['awx'],
        versions['next']['awx-operator'],
    )
)

for product in product_repos:
    version_override = input("Enter the next {} release number ({}): ".format(product, versions['next'][product]))
    if version_override != '':
        versions['next'][product] = version_override

#
# Generate IRC and Mailing list messages
#
print("Enter any known issues (one per line, empty line to end)")
known_issues = []
keep_getting_issues = True
while keep_getting_issues:
    issue = input()
    if issue == '':
        keep_getting_issues = False
    else:
        known_issues.append(issue)

display_known_issues = ''
if len(known_issues) > 0:
    display_known_issues = "\n".join(['Known Issues:'] + ['* {}'.format(item) for item in known_issues])

print(
    '''
Bullhorn/irc list message:

@newsbot We're happy to announce that the next release of AWX, version {0} is now available!
Some notable features include:
{2}

In addition AWX Operator version {1} has also been released!
Some notable features include:
{3}

Please see the releases pages for more details:
AWX: [https://github.com/ansible/awx/releases/tag/{0}](https://github.com/ansible/awx/releases/tag/{0})
Operator: [https://github.com/ansible/awx-operator/releases/tag/{1}](https://github.com/ansible/awx-operator/releases/tag/{1})

{4}
'''.format(
        versions['next']['awx'],
        versions['next']['awx-operator'],
        '\n'.join(versions['release_notes']['awx']),
        '\n'.join(versions['release_notes']['awx-operator']),
        display_known_issues,
    )
)

print(
    '''
Mailing list message:

Subject: Announcing AWX {0} and AWX-Operator {1}
Body:
Hi all,

We're happy to announce that the next release of AWX, version {0} is now available!
Some notable features include:
{2}

In addition AWX Operator version {1} has also been released!
Some notable features include:
{3}

Please see the releases pages for more details:
AWX: https://github.com/ansible/awx/releases/tag/{0}
Operator: https://github.com/ansible/awx-operator/releases/tag/{1}

{4}

-The AWX team.
'''.format(
        versions['next']['awx'],
        versions['next']['awx-operator'],
        '\n'.join(versions['release_notes']['awx']),
        '\n'.join(versions['release_notes']['awx-operator']),
        display_known_issues,
    )
)
