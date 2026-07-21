from ansible_base.resource_registry.workload_identity_client import get_workload_identity_client

__all__ = ['retrieve_workload_identity_jwt_with_claims']


def retrieve_workload_identity_jwt_with_claims(
    claims: dict,
    audience: str,
    scope: str,
    workload_ttl_seconds: int | None = None,
) -> str:
    """Retrieve JWT token from workload claims.
    Raises:
        RuntimeError: if the workload identity client is not configured.
    """
    client = get_workload_identity_client()
    if client is None:
        raise RuntimeError("Workload identity client is not configured")
    kwargs = {"claims": claims, "scope": scope, "audience": audience}
    if workload_ttl_seconds:
        kwargs["workload_ttl_seconds"] = workload_ttl_seconds
    return client.request_workload_jwt(**kwargs).jwt
