# AWX

Hi there! We're excited to have you as a contributor.

Have questions about this document or anything not covered here? Come chat with us at `#ansible-awx` on irc.libera.chat, or submit your question to the [mailing list](https://groups.google.com/forum/#!forum/awx-project).

## Table of contents

- [Things to know prior to submitting code](#things-to-know-prior-to-submitting-code)
- [Setting up your development environment](#setting-up-your-development-environment)
  - [Prerequisites](#prerequisites)
    - [Docker](#docker)
    - [Docker compose](#docker-compose)
    - [Frontend Development](#frontend-development)
  - [Build and Run the Development Environment](#build-and-run-the-development-environment)
    - [Fork and clone the AWX repo](#fork-and-clone-the-awx-repo)
  - [Building API Documentation](#building-api-documentation)
  - [Accessing the AWX web interface](#accessing-the-awx-web-interface)
  - [Purging containers and images](#purging-containers-and-images)
  - [Pre commit hooks](#pre-commit-hooks)
- [What should I work on?](#what-should-i-work-on)
- [Submitting Pull Requests](#submitting-pull-requests)
- [PR Checks run by Zuul](#pr-checks-run-by-zuul)
- [Reporting Issues](#reporting-issues)

## Things to know prior to submitting code

- All code submissions are done through pull requests against the `devel` branch.
- You must use `git commit --signoff` for any commit to be merged, and agree that usage of --signoff constitutes agreement with the terms of [DCO 1.1](./DCO_1_1.md).
- Take care to make sure no merge commits are in the submission, and use `git rebase` vs `git merge` for this reason.
  - If collaborating with someone else on the same branch, consider using `--force-with-lease` instead of `--force`. This will prevent you from accidentally overwriting commits pushed by someone else. For more information, see https://git-scm.com/docs/git-push#git-push---force-with-leaseltrefnamegt
- If submitting a large code change, it's a good idea to join the `#ansible-awx` channel on irc.libera.chat, and talk about what you would like to do or add first. This not only helps everyone know what's going on, it also helps save time and effort, if the community decides some changes are needed.
- We ask all of our community members and contributors to adhere to the [Ansible code of conduct](http://docs.ansible.com/ansible/latest/community/code_of_conduct.html). If you have questions, or need assistance, please reach out to our community team at [codeofconduct@ansible.com](mailto:codeofconduct@ansible.com)

## Setting up your development environment

The AWX development environment workflow and toolchain uses Docker and the docker-compose tool, to provide dependencies, services, and databases necessary to run all of the components. It also bind-mounts the local source tree into the development container, making it possible to observe and test changes in real time.

### Prerequisites

#### Docker

Prior to starting the development services, you'll need `docker` and `docker-compose`. On Linux, you can generally find these in your distro's packaging, but you may find that Docker themselves maintain a separate repo that tracks more closely to the latest releases.

For macOS and Windows, we recommend [Docker for Mac](https://www.docker.com/docker-mac) and [Docker for Windows](https://www.docker.com/docker-windows)
respectively.

For Linux platforms, refer to the following from Docker:

- **Fedora** - https://docs.docker.com/engine/installation/linux/docker-ce/fedora/

- **CentOS** - https://docs.docker.com/engine/installation/linux/docker-ce/centos/

- **Ubuntu** - https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/

- **Debian** - https://docs.docker.com/engine/installation/linux/docker-ce/debian/

- **Arch** - https://wiki.archlinux.org/index.php/Docker

#### Docker Compose

If you're not using Docker for Mac, or Docker for Windows, you may need, or choose to, install the `docker-compose` Python module separately.

```bash
(host)$ pip3 install docker-compose
```

#### Frontend Development

See [the ui development documentation](awx/ui/CONTRIBUTING.md).

#### Fork and clone the AWX repo

If you have not done so already, you'll need to fork the AWX repo on GitHub. For more on how to do this, see [Fork a Repo](https://help.github.com/articles/fork-a-repo/).

### Build and Run the Development Environment

See the [README.md](./tools/docker-compose/README.md) for docs on how to build the awx_devel image and run the development environment.

### Building API Documentation

AWX includes support for building [Swagger/OpenAPI
documentation](https://swagger.io). To build the documentation locally, run:

```bash
(container)/awx_devel$ make swagger
```

This will write a file named `swagger.json` that contains the API specification
in OpenAPI format. A variety of online tools are available for translating
this data into more consumable formats (such as HTML). http://editor.swagger.io
is an example of one such service.

### Accessing the AWX web interface

You can now log into the AWX web interface at [https://localhost:8043](https://localhost:8043), and access the API directly at [https://localhost:8043/api/](https://localhost:8043/api/).

[Create an admin user](./tools/docker-compose/README.md#create-an-admin-user) if needed.

### Purging containers and images

When necessary, remove any AWX containers and images by running the following:

```bash
(host)$ make docker-clean
```

### Pre commit hooks

When you attempt to perform a `git commit` there will be a pre-commit hook that gets run before the commit is allowed to your local repository. For example, python's [black](https://pypi.org/project/black/) will be run to test the formatting of any python files.

While you can use environment variables to skip the pre-commit hooks GitHub will run similar tests and prevent merging of PRs if the tests do not pass.

 If you would like to add additional commit hooks for your own usage you can create a directory in the root of the repository called `pre-commit-user`. Any executable file in that directory will be executed as part of the pre-commit hooks. If any of the pre-commit checks fail the commit will be halted. For your convenience in user scripts, a variable called `CHANGED_FILES` will be set with any changed files present in the commit.

## What should I work on?

For feature work, take a look at the current [Enhancements](https://github.com/ansible/awx/issues?q=is%3Aissue+is%3Aopen+label%3Atype%3Aenhancement).

If it has someone assigned to it then that person is the person responsible for working the enhancement. If you feel like you could contribute then reach out to that person.

Fixing bugs, adding translations, and updating the documentation are always appreciated, so reviewing the backlog of issues is always a good place to start. For extra information on debugging tools, see [Debugging](./docs/debugging/).

**NOTE**

> If you work in a part of the codebase that is going through active development, your changes may be rejected, or you may be asked to `rebase`. A good idea before starting work is to have a discussion with us in the `#ansible-awx` channel on irc.libera.chat, or on the [mailing list](https://groups.google.com/forum/#!forum/awx-project).

**NOTE**

> If you're planning to develop features or fixes for the UI, please review the [UI Developer doc](./awx/ui/README.md).

## Submitting Pull Requests

Fixes and Features for AWX will go through the Github pull request process. Submit your pull request (PR) against the `devel` branch.

Here are a few things you can do to help the visibility of your change, and increase the likelihood that it will be accepted:

- No issues when running linters/code checkers
  - Python: black: `(container)/awx_devel$ make black`
  - Javascript: `(container)/awx_devel$ make ui-lint`
- No issues from unit tests
  - Python: py.test: `(container)/awx_devel$ make test`
  - JavaScript: `(container)/awx_devel$ make ui-test`
- Write tests for new functionality, update/add tests for bug fixes
- Make the smallest change possible
- Write good commit messages. See [How to write a Git commit message](https://chris.beams.io/posts/git-commit/).

It's generally a good idea to discuss features with us first by engaging us in the `#ansible-awx` channel on irc.libera.chat, or on the [mailing list](https://groups.google.com/forum/#!forum/awx-project).

We like to keep our commit history clean, and will require resubmission of pull requests that contain merge commits. Use `git pull --rebase`, rather than
`git pull`, and `git rebase`, rather than `git merge`.

Sometimes it might take us a while to fully review your PR. We try to keep the `devel` branch in good working order, and so we review requests carefully. Please be patient.

All submitted PRs will have the linter and unit tests run against them via Zuul, and the status reported in the PR.

## PR Checks run by Zuul

Zuul jobs for awx are defined in the [zuul-jobs](https://github.com/ansible/zuul-jobs) repo.

Zuul runs the following checks that must pass:

1. `tox-awx-api-lint`
2. `tox-awx-ui-lint`
3. `tox-awx-api`
4. `tox-awx-ui`
5. `tox-awx-swagger`

Zuul runs the following checks that are non-voting (can not pass but serve to inform PR reviewers):

1. `tox-awx-detect-schema-change`
   This check generates the schema and diffs it against a reference copy of the `devel` version of the schema.
   Reviewers should inspect the `job-output.txt.gz` related to the check if their is a failure (grep for `diff -u -b` to find beginning of diff).
   If the schema change is expected and makes sense in relation to the changes made by the PR, then you are good to go!
   If not, the schema changes should be fixed, but this decision must be enforced by reviewers.

## Reporting Issues

We welcome your feedback, and encourage you to file an issue when you run into a problem. But before opening a new issues, we ask that you please view our [Issues guide](./ISSUES.md).
