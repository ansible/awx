# AWX Development Guide

## Project Overview

AWX is a Django REST Framework (DRF) web application that provides a UI, API, and task engine for running Ansible workloads. It is the upstream open-source project for Red Hat Ansible Automation Platform (AAP) Controller.

**Key components:**
- `awx/` — main Django application (API, models, tasks, scheduler)
- `awx_collection/` — Ansible collection providing modules/roles to interact with the AWX API
- `awxkit/` — Python CLI and SDK for AWX (`awx` CLI command)

**Tech stack:**
- Django + Django REST Framework for the API
- PostgreSQL as the primary database
- Redis for caching and messaging
- Celery + receptor for async task execution
- React front-end (served separately during development)

**Target branch for PRs:** `devel`

---

## Local Development Setup

The recommended development environment uses Docker Compose. For full details see
[`tools/docker-compose/README.md`](tools/docker-compose/README.md).

### Prerequisites

- Docker and Docker Compose
- Ansible (for some tooling)
- OpenSSL
- GNU Make

### Starting the Dev Environment

```bash
# Build the development Docker image (skip if pulling from ghcr.io/ansible/awx_devel:devel)
make docker-compose-build

# Start AWX + PostgreSQL + Redis containers
make docker-compose
```

AWX will be available at:
- UI: `https://localhost:8043/`
- API: `https://localhost:8043/api/v2/`

Default credentials: `admin` / `password`

### Common Container Operations

```bash
# Create a superuser
docker exec -ti tools_awx_1 awx-manage createsuperuser

# Load demo organizations, inventories, credentials, and projects
docker exec tools_awx_1 awx-manage create_preload_data

# Open a shell in the AWX container
docker exec -it tools_awx_1 bash
```

### Cluster Mode (Optional)

To simulate a multi-node cluster with execution nodes:

```bash
CONTROL_PLANE_NODE_COUNT=2 EXECUTION_NODE_COUNT=2 make docker-compose
```

### Settings

Django settings live in `awx/settings/`:
- `awx/settings/defaults.py` — base defaults
- `awx/settings/development.py` — development overrides
- `awx/main/tests/settings_for_test.py` — test-specific settings (SQLite, etc.)

See [Settings Management](https://docs.ansible.com/projects/awx/en/latest/contributor/DJANGO_REQUIREMENTS.html#settings-management) in the Django Development Requirements for configuration patterns and external secret loading.

---

## Running Tests

AWX has three test environments depending on what you're testing.

### Unit and Functional Tests

These tests use SQLite and do **not** require any running containers. Run from the repo root.

```bash
# All unit + functional tests (runs in parallel with -n auto)
make test

# Unit tests only
make test_unit
# equivalent to: py.test awx/main/tests/unit awx/conf/tests/unit

# All tests directly with pytest (unit + functional + conf)
py.test awx/main/tests/unit awx/main/tests/functional awx/conf/tests
```

**Running specific tests:**

```bash
# Single file
py.test awx/main/tests/unit/path/to/test_something.py

# Single test class
py.test awx/main/tests/unit/path/to/test_something.py::TestClass

# Single test method
py.test awx/main/tests/unit/path/to/test_something.py::TestClass::test_method

# By keyword
py.test awx/main/tests/unit -k "test_something"
```

**Key pytest flags:**

| Flag | Default | Notes |
|------|---------|-------|
| `--reuse-db` | on | Reuse existing SQLite test database |
| `--create-db` | off | Rebuild SQLite DB from scratch |
| `--nomigrations` | on | Skip Django migrations for speed |
| `--migrations` | off | Run with migrations (needed for migration tests) |
| `-n auto` | on (via `make test`) | Run tests in parallel |

**pytest.ini defaults** (`addopts`):
```
--reuse-db --nomigrations --tb=native
```
`DJANGO_SETTINGS_MODULE` is set to `awx.main.tests.settings_for_test`.

**Functional tests** use `@pytest.mark.django_db` and live in `awx/main/tests/functional/`.
**Unit tests** mock the database and live in `awx/main/tests/unit/`.

### Live Tests

Live tests run against a real PostgreSQL instance and require `make docker-compose` to be running first.
Changes persist in the database between runs.

```bash
make live_test
# equivalent to: cd awx/main/tests/live && py.test tests/
```

### Migration Tests

Tests that verify database schema migrations are consistent:

```bash
make test_migrations
```

This runs pytest with `--migrations -m migration_test --create-db`.

See [Migration Management](https://docs.ansible.com/projects/awx/en/latest/contributor/DJANGO_REQUIREMENTS.html#migration-management) in the Django Development Requirements — the key rule is: **do not rewrite migrations**, and include a reverse migration where possible.

### Test Coverage

```bash
make test_coverage
```

This adds `--cov --cov-report=xml --junitxml=reports/junit.xml` and rebuilds the DB.
Reports are written to `reports/coverage.xml` and `reports/junit.xml`.

See [Coverage Requirements](https://docs.ansible.com/projects/awx/en/latest/contributor/DJANGO_REQUIREMENTS.html#coverage-requirements) — targets are 75% overall, 95% for test code, and 100% for new patches.

### Collection and awxkit Tests

For testing the Ansible collection (`awx_collection/`) and the `awxkit` CLI/SDK, see:
[`docs/development/collection-awxkit-tests.md`](docs/development/collection-awxkit-tests.md)

### Test Factories and Fixtures

- `awx/main/tests/factories/` — factory utilities for creating test objects (jobs, inventories, credentials, etc.)
- `awx/main/tests/conftest.py` — shared pytest fixtures

See [`awx/main/tests/README.md`](awx/main/tests/README.md) for more on the test environment.

---

## Code Quality

### Formatting

AWX uses [Black](https://black.readthedocs.io/) for Python formatting with a line length of 160.
Black is configured in `pyproject.toml` and excludes `awx_collection/`.

```bash
# Auto-format all Python files
make black
```

### Linting

```bash
# Run black check + flake8
make check

# Full linter suite (black, flake8, yamllint, etc.)
tox -e linters
```

YAML files are linted with yamllint.

### Pre-commit Hook

A pre-commit hook is auto-installed at `.git/hooks/pre-commit` and runs `black --check` before
each commit. To skip it in exceptional circumstances:

```bash
AWX_IGNORE_BLACK=1 git commit -m "..."
```

### Commit Requirements

- **DCO sign-off required:** `git commit --signoff` (Developer Certificate of Origin 1.1)
- **No merge commits:** always rebase instead of merging
  ```bash
  git fetch origin devel
  git rebase origin/devel
  ```

---

## Codebase Navigation

### Core Application (`awx/main/`)

| Path | Purpose |
|------|---------|
| `awx/main/models/` | Django ORM models — job templates, jobs, inventory, credentials, organizations, workflow, etc. |
| `awx/main/views/` | DRF API views (list/detail) |
| `awx/main/serializers/` | DRF serializers — validation and representation |
| `awx/main/access.py` | RBAC access control logic — who can do what |
| `awx/main/tasks/` | Celery async task definitions (job launching, inventory sync, etc.) |
| `awx/main/scheduler/` | Task manager and job scheduling logic |
| `awx/main/signals.py` | Django signals |
| `awx/main/migrations/` | Database migrations |
| `awx/main/urls.py` | URL routing for the API |

When working on these components, consult:
- [Model Design](https://docs.ansible.com/projects/awx/en/latest/contributor/DJANGO_REQUIREMENTS.html#model-design) — abstract base models, mixin architecture, domain-based file organization
- [REST API Design Standards](https://docs.ansible.com/projects/awx/en/latest/contributor/API_REQUIREMENTS.html#rest-api-design-standards) — URL patterns, HTTP method usage, response time targets
- [Serialization and Data Validation](https://docs.ansible.com/projects/awx/en/latest/contributor/API_REQUIREMENTS.html#serialization-and-data-validation) — base serializer patterns, custom field types, validation
- [Authentication and Authorization](https://docs.ansible.com/projects/awx/en/latest/contributor/API_REQUIREMENTS.html#authentication-and-authorization) — RBAC, permission classes, logging requirements

### Configuration

| Path | Purpose |
|------|---------|
| `awx/conf/` | Tower configuration / settings framework (dynamic settings stored in DB) |
| `awx/settings/` | Static Django settings (base, development, production) |
| `awx/main/tests/settings_for_test.py` | Test-specific Django settings (SQLite, disabled tasks, etc.) |

### Tests

| Path | Purpose |
|------|---------|
| `awx/main/tests/unit/` | Unit tests (mocked DB) |
| `awx/main/tests/functional/` | Functional tests (SQLite DB, `@pytest.mark.django_db`) |
| `awx/main/tests/live/` | Live tests (real PostgreSQL, requires running stack) |
| `awx/main/tests/factories/` | Factory helpers for test object creation |
| `awx/main/tests/conftest.py` | Shared pytest fixtures |

### Sub-components

| Path | Purpose |
|------|---------|
| `awx_collection/` | Ansible collection — modules, roles, plugins for interacting with AWX API |
| `awxkit/` | Python SDK and `awx` CLI tool |
| `tools/docker-compose/` | Docker Compose files and scripts for the dev environment |
| `docs/` | Architecture docs, debugging guides, feature documentation |

### Finding Things Quickly

```bash
# Find model for a resource (e.g., JobTemplate)
grep -r "class JobTemplate" awx/main/models/

# Find the view for an API endpoint
grep -r "JobTemplateList\|JobTemplateDetail" awx/main/views/

# Find all access control checks for a resource
grep -r "class JobTemplateAccess" awx/main/access.py

# Find a Celery task
grep -r "def task_name" awx/main/tasks/
```

---

## AI Agent Permissions

A list of commands that may be run automatically and commands that require explicit user confirmation
is maintained in [`docs/development/ai-agent-commands.md`](docs/development/ai-agent-commands.md).

**Key rules:**
- Most read, test, lint, and inspect commands are safe to run without asking.
- Live tests must run inside the `tools_awx_1` container (they require a running PostgreSQL instance).
- Never run `git push`, `git reset --hard`, `git restore`, or any `gh` (GitHub CLI) command without explicit user approval.

---

## Contributing

1. **Fork and branch** from `devel`
2. **Sign your commits:** `git commit --signoff`
3. **Rebase, don't merge:** keep history linear
4. **Format before committing:** `make black`
5. **Run tests:** `make test` (unit + functional)
6. **Open a PR** against the `devel` branch

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full contribution guidelines, including the DCO
agreement, PR process, and coding standards.

Before opening a PR, ensure your changes comply with:
- [API Development Requirements](https://docs.ansible.com/projects/awx/en/latest/contributor/API_REQUIREMENTS.html) — for any changes to views, serializers, authentication, or API endpoints
- [Django Development Requirements](https://docs.ansible.com/projects/awx/en/latest/contributor/DJANGO_REQUIREMENTS.html) — for changes to models, settings, migrations, middleware, or project structure

---

## Further Reading

| Resource | Description |
|----------|-------------|
| [`tools/docker-compose/README.md`](tools/docker-compose/README.md) | Full Docker dev environment guide |
| [`awx/main/tests/README.md`](awx/main/tests/README.md) | Test environment details |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution guidelines and DCO |
| [`docs/development/collection-awxkit-tests.md`](docs/development/collection-awxkit-tests.md) | Collection and awxkit test guide |
| [`docs/`](docs/) | Architecture, debugging, and feature documentation |
| [API Development Requirements](https://docs.ansible.com/projects/awx/en/latest/contributor/API_REQUIREMENTS.html) | Standards for DRF API design, authentication, serialization, performance, and security |
| [Django Development Requirements](https://docs.ansible.com/projects/awx/en/latest/contributor/DJANGO_REQUIREMENTS.html) | Standards for project structure, models, settings, migrations, middleware, and testing |
