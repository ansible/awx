
Making API changes
==================

AWX keeps a committed OpenAPI spec (``openapi.yaml`` at the repository
root, generated with `drf-spectacular <https://github.com/tfranzel/drf-spectacular>`_)
and runs CI checks on pull requests that change the REST API. This
document covers the contributor workflow around those checks.

.. contents::
    :local:

What CI enforces on your pull request
--------------------------------------

Three checks run on pull requests that touch the API surface:

- **Breaking change detection** — if your pull request modifies
  ``openapi.yaml``, `oasdiff <https://github.com/oasdiff/oasdiff>`_
  compares it against the base branch and blocks the pull request when a
  schema-level breaking change is detected. The result is posted as a
  pull request comment.
- **Changelog fragment enforcement** — a pull request that modifies
  ``openapi.yaml`` must include a changelog fragment (see
  `Changelog fragments`_). CI posts a pre-filled skeleton as a comment
  if the spec changed and no fragment is present.
- **Schema drift detection** — the spec is regenerated from code and
  compared against the committed ``openapi.yaml``. If you changed the
  API in code but did not regenerate and commit the spec, this check
  fails.

One gap to be aware of: behavioral changes — changes to what an
endpoint *does* rather than its schema — are invisible to these checks.
If your change alters endpoint behavior, sorting, pagination, side
effects, or error semantics, describe it in the pull request so
reviewers can evaluate it.

Making an API change
--------------------

When you change an API endpoint, regenerate and commit the spec::

    (host)$ COMPOSE_TAG=devel make docker-compose-build        # first time, or when requirements change
    (host)$ COMPOSE_TAG=devel make docker-runner AWX_DOCKER_CMD="make genschema"
    (host)$ git add openapi.yaml

This runs drf-spectacular (``awx-manage spectacular``) and writes
``openapi.yaml`` at the repository root. ``COMPOSE_TAG=devel`` is
required because it defaults to your git branch name, but only the
``devel`` tag exists — ``docker-runner`` mounts the repository at
``/awx_devel`` and runs ``genschema`` inside that container.

To preview what the schema drift check will report before pushing,
regenerate and diff against the base branch's committed spec::

    (host)$ COMPOSE_TAG=devel make docker-runner AWX_DOCKER_CMD="make detect-schema-change SCHEMA_DIFF_BASE_BRANCH=devel"

Changelog fragments
-------------------

Every consumer-visible API change is documented in a YAML fragment file
in ``changelogs/fragments/``, named ``YYYYMMDD-<short-description>.yaml``.
One fragment per consumer-visible change; unrelated changes in the same
pull request use separate fragments.

.. code-block:: yaml

    # changelogs/fragments/20260915-remove-legacy-credential-field.yaml
    title: "Remove legacy credential field from job template response"
    type:
      - removed
    breaking: true
    summary: |
      The `credentials` list field replaces the `credential` field on
      `/api/v2/job_templates/` responses. Before this update, a single
      `credential` field was returned. The `credentials` list field supports
      multiple credentials per job template.
    endpoint:
      - "/api/v2/job_templates/{id}/"
    migration: |
      Replace references to `response.credential` with `response.credentials[0].id`
      for single-credential workflows, or iterate `response.credentials` for
      multi-credential support.

Required fields are ``title``, ``type``, ``breaking``, and ``summary``.
The ``migration`` field is required for breaking changes and
deprecations. The JSON Schema in the CI workflow is the definitive
source of allowed values.

CI validates any fragment created or modified by the pull request
against the schema. If the spec changed and no fragment exists, CI
generates a skeleton with oasdiff and posts it as a comment for you to
complete. Behavioral changes that do not touch the spec cannot be
auto-detected — the fragment is your responsibility in that case.

Breaking changes
----------------

The breaking change check exists because AWX API consumers depend on
the stability of the ``/api/v2/`` surface. If oasdiff flags your pull
request as breaking and you believe the change is unavoidable, do not
work around the check — open a discussion with the maintainers on the
`Ansible Forum <https://forum.ansible.com/tag/awx>`_ or in the pull
request first. When a breaking change has been approved through the
internal review process, a maintainer applies the
``breaking-change-approved`` label to the pull request, and the check
passes.

What happens on merge
---------------------

When a pull request that changes ``openapi.yaml`` merges into ``devel``:

- The committed spec is synced to the central ``aap-openapi-specs``
  repository, which holds the specs for all AAP services.
- The spec is uploaded to S3, where the documentation build downloads
  it to render the API reference.
