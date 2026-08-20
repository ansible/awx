# Generated with Claude Opus 4.6
"""In-memory data structures for the job preparation phase.

TaskPrepData eagerly loads the associated Django objects that a job needs
in order to build the private_data_dir (credentials, execution environment,
galaxy credentials, etc.). Once constructed, the prep phase can run without
further DB queries for those objects.

Not in scope:
- Large data movements. Inventories can have tens of thousands of hosts,
  so writing the inventory file is handled by dedicated code in the job
  prep path, not cached here. Same for host facts.
- Later lifecycle stages. Transmitting to receptor, reading results back,
  and post-run hooks operate on the raw instance after prep is discarded.
- The associated project sync. Fetching source onto the execution node
  runs as a separate task over receptor and does not use this object.

Key invariants:
- Credentials are fetched from the DB exactly once and owned here.
- OIDC JWTs are generated once and stored in TaskPrepData.workload_tokens.
  The Credential model itself has no runtime state.
- No method on these classes triggers a credential re-fetch.
"""

from __future__ import annotations

from typing import Literal

from django.db.models import Model


class PreparedCredential:
    """Credential wrapper that injects runtime context for dynamic fields.

    Delegates most access to the underlying Credential model. The key
    difference is ``get_input``: for dynamic fields (those backed by a
    CredentialInputSource), it resolves them through the parent
    TaskPrepData's ``workload_tokens`` dict, which holds OIDC JWTs
    and similar runtime values keyed by input source PK.

    Hashes by pk, so it interoperates with raw Credential objects as
    dict keys (Django Model.__hash__ is also hash(pk)).
    """

    def __init__(self, credential, prep_data):
        self._credential = credential
        self._prep_data = prep_data

    def get_input(self, field_name, **kwargs):
        """Get an input value, injecting runtime context for dynamic fields.

        For dynamic fields (those backed by a CredentialInputSource), the
        input source backend is called with workload tokens from the parent
        TaskPrepData so that internal fields like workload_identity_token
        are available.

        For all other fields, delegates to the Credential model's get_input
        which handles decryption, defaults, etc.
        """
        if (
            self._credential.credential_type.kind != "external"
            and field_name in self._credential.dynamic_input_fields
        ):
            return self._get_dynamic_input(field_name)
        return self._credential.get_input(field_name, **kwargs)

    def _get_dynamic_input(self, field_name):
        for input_source in self._credential.input_sources.all():
            if input_source.input_field_name == field_name:
                return input_source.get_input_value(
                    context=self._prep_data.workload_tokens
                )
        raise ValueError("{} is not a dynamic input field".format(field_name))

    def __getattr__(self, name):
        return getattr(self._credential, name)

    def __hash__(self):
        return hash(self._credential.pk)

    def __eq__(self, other):
        if isinstance(other, PreparedCredential):
            return self._credential.pk == other._credential.pk
        # Allow comparison with raw Credential objects.
        # Django's Model.__eq__ returns NotImplemented for non-Model types,
        # so Python falls through to this side.
        return self._credential.pk == getattr(other, "pk", None)

    def __repr__(self):
        return f"PreparedCredential(pk={self._credential.pk}, kind={self.kind})"


class TaskPrepData:
    """Eagerly loaded snapshot of associated Django objects for job prep.

    Created once from a UnifiedJob instance via ``from_instance()``.
    Construction resolves the execution environment, fetches credentials
    and galaxy credentials from the DB, and caches the parent workflow
    job ID — all the small associated objects the build methods need.

    Attribute access falls through to the underlying instance via
    ``__getattr__``, so build_env/build_args/injector code can read
    instance fields (pk, source, playbook, job_type, etc.) without
    change. Credential access goes through the owned lists, never
    back to the DB.

    Discarded after private_data_dir and runner kwargs are fully built.
    """

    _TASK_KIND_MAP = {
        "job": "job",
        "jobtemplate": "job",
        "projectupdate": "project",
        "project": "project",
        "inventoryupdate": "inventory",
        "inventorysource": "inventory",
        "adhoccommand": "adhoc",
        "systemjob": "system",
        "systemjobtemplate": "system",
    }

    def __init__(
        self, instance: Model, credentials: list[Model], galaxy_credentials: list[Model]
    ):
        self._instance = instance
        self.workload_tokens = {}
        self.parent_workflow_job_id = None
        self.credentials = [PreparedCredential(c, self) for c in credentials]
        self.galaxy_credentials = [
            PreparedCredential(c, self) for c in galaxy_credentials
        ]

    @property
    def task_kind(self) -> Literal["job", "project", "inventory", "adhoc", "system"]:
        return self._TASK_KIND_MAP[self._instance._meta.model_name]

    @classmethod
    def from_instance(cls, instance):
        """Create a TaskPrepData from a UnifiedJob instance.

        Resolves the execution environment (if not already set),
        fetches credentials exactly once from the DB, and caches
        the parent workflow job ID. Uses the FK ``credential`` for
        ProjectUpdate, or the M2M ``credentials`` for all other types.
        """
        # Resolve EE before anything else — this is a DB write
        if instance.execution_environment_id is None:
            from awx.main.signals import disable_activity_stream

            with disable_activity_stream():
                instance.execution_environment = (
                    instance.resolve_execution_environment()
                )
                instance.save(update_fields=["execution_environment"])

        if instance._meta.model_name in ("projectupdate", "adhoccommand"):
            creds = (
                [instance.credential] if instance.__dict__.get("credential_id") else []
            )
        else:
            creds = list(
                instance.credentials.prefetch_related(
                    "input_sources__source_credential"
                ).all()
            )

        galaxy_creds = []
        if (
            hasattr(instance, "project")
            and instance.project
            and instance.project.organization
        ):
            galaxy_creds = list(
                instance.project.organization.galaxy_credentials.prefetch_related(
                    "input_sources__source_credential"
                ).all()
            )

        prep = cls(instance, creds, galaxy_credentials=galaxy_creds)

        # Cache workflow job ID to avoid FK lazy-load later
        if instance.spawned_by_workflow:
            wf_job = instance.get_workflow_job()
            if wf_job:
                prep.parent_workflow_job_id = wf_job.id

        return prep

    @classmethod
    def for_testing(cls, instance, credentials, workload_tokens=None):
        """Create TaskPrepData with pre-populated workload tokens for tests.

        Use this when testing code that consumes workload tokens (e.g.
        dynamic input resolution) without running the full OIDC flow.
        """
        prep = cls(instance, credentials, galaxy_credentials=[])
        if workload_tokens:
            prep.workload_tokens.update(workload_tokens)
        return prep

    def get_cloud_credential(self):
        """Return the credential tied to the inventory source type.

        In-memory replacement for InventoryUpdate.get_cloud_credential().
        Returns from the owned credentials list, never hits the DB.
        Returns None for job types that don't have a source.
        """
        injector_kind = getattr(self._instance, "injector_credential_kind", None)
        if injector_kind is None:
            return None
        kind = injector_kind()
        if kind is None:
            # source exists but has no dedicated injector
            # fall back to first non-vault credential
            for cred in self.credentials:
                if cred.credential_type.kind != "vault":
                    return cred
            return None
        for cred in self.credentials:
            if cred.kind == kind:
                return cred
        return None

    def credentials_of_kind(self, kind):
        """Return credentials matching the given credential type kind."""
        return [c for c in self.credentials if c.credential_type.kind == kind]

    def get_credentials_for_injection(self):
        """Return credentials for the generic credential type injection loop.

        Excludes credentials that are already handled by custom build logic:
        - AdHocCommand and ProjectUpdate: FK credential is handled entirely
          by the subclass build methods, not the generic injection loop.
        - InventoryUpdate: the cloud credential matching injector_credential_kind
          is handled by the inventory source injector.
        """
        if self.task_kind in ("adhoc", "project"):
            return []
        injector_kind = getattr(self._instance, "injector_credential_kind", None)
        if injector_kind is None:
            return self.credentials
        kind = injector_kind()
        if kind is None:
            return self.credentials
        return [c for c in self.credentials if c.kind != kind]

    def __getattr__(self, name):
        return getattr(self._instance, name)
