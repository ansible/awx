import argparse
import os
from typing import OrderedDict
import pyexcel
import requests
import sys


def get_headers():
    access_token_env_var = "GITHUB_ACCESS_TOKEN"
    if access_token_env_var in os.environ:
        access_token = os.environ[access_token_env_var]
        return {"Authorization": f"token {access_token}"}
    else:
        print(f"{access_token_env_var} not present, performing unathenticated calls that might hit rate limits.")
        return None


def fetch_items(url, params, headers):
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response
    else:
        print(f"Failed to fetch items: {response.status_code}", file=sys.stderr)
        print(f"{response.content}", file=sys.stderr)
        return None


def extract_next_url(response):
    if 'Link' in response.headers:
        links = response.headers['Link'].split(',')
        for link in links:
            if 'rel="next"' in link:
                return link.split(';')[0].strip('<> ')
    return None


def get_all_items(url, params, limit=None):
    items = []
    headers = get_headers()
    while url:
        response = fetch_items(url, params, headers)
        if response:
            items.extend(response.json())
            print(f"Processing {len(items)}", file=sys.stderr)
            if limit and len(items) > limit:
                break
            url = extract_next_url(response)
        else:
            url = None
    return items


def get_open_issues(repo_url, limit):
    owner, repo = repo_url.rstrip('/').split('/')[-2:]
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {'state': 'open', 'per_page': 100}
    issues = get_all_items(url, params, limit)
    open_issues = [issue for issue in issues if 'pull_request' not in issue]
    return open_issues


def get_open_pull_requests(repo_url, limit):
    owner, repo = repo_url.rstrip('/').split('/')[-2:]
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {'state': 'open', 'per_page': 100}
    pull_requests = get_all_items(url, params, limit)
    return pull_requests


def generate_ods(issues, pull_requests, filename, people):
    data = OrderedDict()

    # Prepare issues data
    issues_data = []
    for n, issue in enumerate(issues):
        issues_data.append(
            [
                issue['html_url'],
                issue['title'],
                issue['created_at'],
                issue['user']['login'],
                issue['assignee']['login'] if issue['assignee'] else 'None',
                people[n % len(people)],
            ]
        )
    issues_headers = ['url', 'title', 'created_at', 'user', 'assignee', 'action']
    issues_data.insert(0, issues_headers)
    data.update({"Issues": issues_data})

    # Prepare pull requests data
    prs_data = []
    for n, pr in enumerate(pull_requests):
        prs_data.append(
            [pr['html_url'], pr['title'], pr['created_at'], pr['user']['login'], pr['assignee']['login'] if pr['assignee'] else 'None', people[n % len(people)]]
        )
    prs_headers = ['url', 'title', 'created_at', 'user', 'assignee', 'action']
    prs_data.insert(0, prs_headers)
    data.update({"Pull Requests": prs_data})

    # Save to ODS file
    pyexcel.save_book_as(bookdict=data, dest_file_name=filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="minimum number of issues/PRs to pull [Pulls all by default]", default=None)
    parser.add_argument("--out", type=str, help="output file name [awx_community-triage.ods]", default="awx_community-triage.ods")
    parser.add_argument("--repository-url", type=str, help="repository url [https://github.com/ansible/awx]", default="https://github.com/ansible/awx")
    parser.add_argument("--people", type=str, help="comma separated list of names to distribute the issues/PRs among [Alice,Bob]", default="Alice,Bob")
    args = parser.parse_args()
    limit = args.limit
    output_file_name = args.out
    repo_url = args.repository_url
    people = str(args.people).split(",")
    open_issues = get_open_issues(repo_url, limit)
    open_pull_requests = get_open_pull_requests(repo_url, limit)
    print(f"Open issues: {len(open_issues)}")
    print(f"Open Pull Requests: {len(open_pull_requests)}")
    generate_ods(open_issues, open_pull_requests, output_file_name, people)
    print(f"Generated {output_file_name} with open issues and pull requests.")


if __name__ == "__main__":
    main()
