# Testing the AWX Collection and awxkit

This document covers testing for two sub-components of AWX:

- **`awx_collection/`** — the Ansible collection providing modules and roles for interacting with the AWX API
- **`awxkit/`** — the Python SDK and `awx` CLI tool

For unit and functional test guidance on the main AWX application, see [`awx/main/tests/README.md`](../../awx/main/tests/README.md).

---

## awx_collection Tests

The collection ships three categories of tests: unit tests (run via pytest), sanity tests
(run via `ansible-test`), and integration tests (run against a live AWX instance).

### Unit Tests

These run the collection's Python module code directly through pytest. No running AWX instance
is required.

```bash
make test_collection
```

This command:
1. Installs `ansible-core` if not already present
2. Runs `py.test` against `COLLECTION_TEST_DIRS` with coverage

### Sanity Tests

Ansible sanity tests validate collection structure, documentation, and coding standards using
`ansible-test`. No running AWX instance is required.

```bash
make test_collection_sanity
```

This command:
1. Removes any previous build artifacts in `awx_collection_build/` and `$(COLLECTION_INSTALL)`
2. Installs `ansible-core` if not already present
3. Builds and installs the collection at version `1.0.0`
4. Runs `ansible-test sanity`

Common sanity checks include:
- PEP 8 / code style
- Module documentation validation (argument specs, examples, return docs)
- Import validation

### Integration Tests

Integration tests run collection modules against a real AWX instance. **A running AWX deployment
is required** (see the [Docker Compose dev setup](../../CLAUDE.md#local-development-setup)).

```bash
make test_collection_integration
```

This command:
1. Installs the collection via `make install_collection`
2. Runs `ansible-test integration` with Python version matching `ANSIBLE_TEST_PYTHON_VERSION`
3. Generates a coverage XML report

**Prerequisites:**
- AWX running and accessible (typically `https://localhost:8043/`)
- Controller credentials configured for `ansible-test` (set via `CONTROLLER_HOST`,
  `CONTROLLER_USERNAME`, `CONTROLLER_PASSWORD` environment variables or an integration config)
- `ansible-core` installed in your environment

**Running a specific integration test target:**

```bash
# Set COLLECTION_TEST_TARGET to run only one module's tests
COLLECTION_TEST_TARGET=tower_job_template make test_collection_integration
```

### Collection Test Layout

```
awx_collection/
├── plugins/
│   ├── modules/          # Collection modules (one file per resource)
│   ├── module_utils/     # Shared utilities (api.py, controller_api.py, etc.)
│   └── lookup/           # Lookup plugins
└── tests/
    ├── unit/             # pytest unit tests for modules
    └── integration/
        └── targets/      # ansible-test integration test targets (one per module)
```

---

## awxkit Tests

`awxkit` is the Python SDK and CLI for AWX. It has its own `tox` configuration and test suite.

### Running awxkit Tests

```bash
cd awxkit && tox -re py3
```

This runs the awxkit test suite in a fresh virtual environment using the default Python 3
interpreter. The `-r` flag forces tox to recreate the environment (useful after dependency
changes); omit it for faster re-runs:

```bash
cd awxkit && tox -e py3
```

`make test` (at the repo root) also runs `cd awxkit && tox -re py3` as part of its full suite.

### awxkit Test Layout

```
awxkit/
├── awxkit/               # SDK source (api/, cli/, etc.)
├── tests/                # awxkit tests
├── tox.ini               # tox configuration
└── setup.py
```

### awxkit CLI Usage (for manual testing)

After installing awxkit (`pip install -e awxkit/`), the `awx` CLI is available:

```bash
# Configure target and credentials
export CONTROLLER_HOST=https://localhost:8043
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=password

# List job templates
awx job_templates list

# Launch a job
awx job_templates launch <id>
```

---

## CI Workflow

In GitHub Actions, the following jobs run automatically on pull requests:

| Job | Command | Requires Live AWX |
|-----|---------|-------------------|
| Unit + functional tests | `make test` | No |
| Collection unit tests | `make test_collection` | No |
| Collection sanity tests | `make test_collection_sanity` | No |
| Collection integration tests | `make test_collection_integration` | Yes |
| Migration tests | `make test_migrations` | No |
| Linting | `tox -e linters` | No |

Integration tests in CI run against a deployment spun up as part of the CI pipeline. When
running locally, you need your own AWX instance.

Coverage reports are written to:
- `reports/coverage.xml` — main AWX coverage
- `awxkit/coverage.xml` — awxkit coverage
- `reports/junit.xml` — JUnit test results
