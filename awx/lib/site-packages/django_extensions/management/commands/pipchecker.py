import os
import pip
import sys
import json
import urllib2
import urlparse
import xmlrpclib
from distutils.version import LooseVersion
from django.core.management.base import NoArgsCommand
from django_extensions.management.color import color_style
from optparse import make_option
from pip.req import parse_requirements

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            "-t", "--github-api-token", action="store", dest="github_api_token",
            help="A github api authentication token."
        ),
        make_option(
            "-r", "--requirement", action="append", dest="requirements",
            default=[], metavar="FILENAME",
            help="Check all the packages listed in the given requirements file. "
                 "This option can be used multiple times."
        ),
        make_option(
            "-n", "--newer", action="store_true", dest="show_newer",
            help="Also show when newer version then available is installed."
        ),
    )
    help = "Scan pip requirement files for out-of-date packages."

    def handle_noargs(self, **options):
        self.style = color_style()

        self.options = options
        if options["requirements"]:
            req_files = options["requirements"]
        elif os.path.exists("requirements.txt"):
            req_files = ["requirements.txt"]
        elif os.path.exists("requirements"):
            req_files = ["requirements/{0}".format(f) for f in os.listdir("requirements")
                         if os.path.isfile(os.path.join("requirements", f)) and
                         f.lower().endswith(".txt")]
        else:
            sys.exit("requirements not found")

        self.reqs = {}
        for filename in req_files:
            class Object(object):
                pass
            mockoptions = Object()
            mockoptions.default_vcs = "git"
            mockoptions.skip_requirements_regex = None
            for req in parse_requirements(filename, options=mockoptions):
                self.reqs[req.name] = {
                    "pip_req": req,
                    "url": req.url,
                }

        if options["github_api_token"]:
            self.github_api_token = options["github_api_token"]
        elif os.environ.get("GITHUB_API_TOKEN"):
            self.github_api_token = os.environ.get("GITHUB_API_TOKEN")
        else:
            self.github_api_token = None  # only 50 requests per hour

        self.check_pypi()
        if HAS_REQUESTS:
            self.check_github()
        else:
            print(self.style.ERROR("Cannot check github urls. The requests library is not installed. ( pip install requests )"))
        self.check_other()

    def _urlopen_as_json(self, url, headers=None):
        """Shorcut for return contents as json"""
        req = urllib2.Request(url, headers=headers)
        return json.loads(urllib2.urlopen(req).read())

    def check_pypi(self):
        """
        If the requirement is frozen to pypi, check for a new version.
        """
        for dist in pip.get_installed_distributions():
            name = dist.project_name
            if name in self.reqs.keys():
                self.reqs[name]["dist"] = dist

        pypi = xmlrpclib.ServerProxy("http://pypi.python.org/pypi")
        for name, req in self.reqs.items():
            if req["url"]:
                continue  # skipping github packages.
            elif "dist" in req:
                dist = req["dist"]
                dist_version = LooseVersion(dist.version)
                available = pypi.package_releases(req["pip_req"].url_name)
                try:
                    available_version = LooseVersion(available[0])
                except IndexError:
                    available_version = None

                if not available_version:
                    msg = self.style.WARN("release is not on pypi (check capitalization and/or --extra-index-url)")
                elif self.options['show_newer'] and dist_version > available_version:
                    msg = self.style.INFO("{0} available (newer installed)".format(available_version))
                elif available_version > dist_version:
                    msg = self.style.INFO("{0} available".format(available_version))
                else:
                    msg = "up to date"
                    del self.reqs[name]
                    continue
                pkg_info = self.style.BOLD("{dist.project_name} {dist.version}".format(dist=dist))
            else:
                msg = "not installed"
                pkg_info = name
            print("{pkg_info:40} {msg}".format(pkg_info=pkg_info, msg=msg))
            del self.reqs[name]

    def check_github(self):
        """
        If the requirement is frozen to a github url, check for new commits.

        API Tokens
        ----------
        For more than 50 github api calls per hour, pipchecker requires
        authentication with the github api by settings the environemnt
        variable ``GITHUB_API_TOKEN`` or setting the command flag
        --github-api-token='mytoken'``.

        To create a github api token for use at the command line::
             curl -u 'rizumu' -d '{"scopes":["repo"], "note":"pipchecker"}' https://api.github.com/authorizations

        For more info on github api tokens:
            https://help.github.com/articles/creating-an-oauth-token-for-command-line-use
            http://developer.github.com/v3/oauth/#oauth-authorizations-api

        Requirement Format
        ------------------
        Pipchecker gets the sha of frozen repo and checks if it is
        found at the head of any branches. If it is not found then
        the requirement is considered to be out of date.

        Therefore, freezing at the commit hash will provide the expected
        results, but if freezing at a branch or tag name, pipchecker will
        not be able to determine with certainty if the repo is out of date.

        Freeze at the commit hash (sha)::
            git+git://github.com/django/django.git@393c268e725f5b229ecb554f3fac02cfc250d2df#egg=Django

        Freeze with a branch name::
            git+git://github.com/django/django.git@master#egg=Django

        Freeze with a tag::
            git+git://github.com/django/django.git@1.5b2#egg=Django

        Do not freeze::
            git+git://github.com/django/django.git#egg=Django

        """
        for name, req in self.reqs.items():
            req_url = req["url"]
            if not req_url:
                continue
            if req_url.startswith("git") and "github.com/" not in req_url:
                continue
            if req_url.endswith(".tar.gz") or req_url.endswith(".tar.bz2") or req_url.endswith(".zip"):
                continue

            headers = {
                "content-type": "application/json",
            }
            if self.github_api_token:
                headers["Authorization"] = "token {0}".format(self.github_api_token)
            try:
                user, repo = urlparse.urlparse(req_url).path.split("#")[0].strip("/").rstrip("/").split("/")
            except (ValueError, IndexError) as e:
                print(self.style.ERROR("\nFailed to parse %r: %s\n" % (req_url, e)))
                continue

            try:
                #test_auth = self._urlopen_as_json("https://api.github.com/django/", headers=headers)
                test_auth = requests.get("https://api.github.com/django/", headers=headers).json()
            except urllib2.HTTPError as e:
                print("\n%s\n" % str(e))
                return

            if "message" in test_auth and test_auth["message"] == "Bad credentials":
                print(self.style.ERROR("\nGithub API: Bad credentials. Aborting!\n"))
                return
            elif "message" in test_auth and test_auth["message"].startswith("API Rate Limit Exceeded"):
                print(self.style.ERROR("\nGithub API: Rate Limit Exceeded. Aborting!\n"))
                return

            frozen_commit_sha = None
            if ".git" in repo:
                repo_name, frozen_commit_full = repo.split(".git")
                if frozen_commit_full.startswith("@"):
                    frozen_commit_sha = frozen_commit_full[1:]
            elif "@" in repo:
                repo_name, frozen_commit_sha = repo.split("@")

            if frozen_commit_sha is None:
                msg = self.style.ERROR("repo is not frozen")

            if frozen_commit_sha:
                branch_url = "https://api.github.com/repos/{0}/{1}/branches".format(user, repo_name)
                #branch_data = self._urlopen_as_json(branch_url, headers=headers)
                branch_data = requests.get(branch_url, headers=headers).json()

                frozen_commit_url = "https://api.github.com/repos/{0}/{1}/commits/{2}".format(
                    user, repo_name, frozen_commit_sha
                )
                #frozen_commit_data = self._urlopen_as_json(frozen_commit_url, headers=headers)
                frozen_commit_data = requests.get(frozen_commit_url, headers=headers).json()

                if "message" in frozen_commit_data and frozen_commit_data["message"] == "Not Found":
                    msg = self.style.ERROR("{0} not found in {1}. Repo may be private.".format(frozen_commit_sha[:10], name))
                elif frozen_commit_sha in [branch["commit"]["sha"] for branch in branch_data]:
                    msg = self.style.BOLD("up to date")
                else:
                    msg = self.style.INFO("{0} is not the head of any branch".format(frozen_commit_data["sha"][:10]))

            if "dist" in req:
                pkg_info = "{dist.project_name} {dist.version}".format(dist=req["dist"])
            elif frozen_commit_sha is None:
                pkg_info = name
            else:
                pkg_info = "{0} {1}".format(name, frozen_commit_sha[:10])
            print("{pkg_info:40} {msg}".format(pkg_info=pkg_info, msg=msg))
            del self.reqs[name]

    def check_other(self):
        """
        If the requirement is frozen somewhere other than pypi or github, skip.

        If you have a private pypi or use --extra-index-url, consider contributing
        support here.
        """
        if self.reqs:
            print(self.style.ERROR("\nOnly pypi and github based requirements are supported:"))
            for name, req in self.reqs.items():
                if "dist" in req:
                    pkg_info = "{dist.project_name} {dist.version}".format(dist=req["dist"])
                elif "url" in req:
                    pkg_info = "{url}".format(url=req["url"])
                else:
                    pkg_info = "unknown package"
                print(self.style.BOLD("{pkg_info:40} is not a pypi or github requirement".format(pkg_info=pkg_info)))
