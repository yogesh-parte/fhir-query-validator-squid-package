"""
Workflow identity resolution — avoid trusting client-supplied user_id in production.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional


def trust_client_user_id() -> bool:
    """
    When true (default), workflow accepts client-supplied user_id for demos/tests.
    Set FHIR_TRUST_CLIENT_USER_ID=false in production to derive identity server-side.
    """
    return os.getenv("FHIR_TRUST_CLIENT_USER_ID", "true").lower() == "true"


def resolve_workflow_user_id(
    client_user_id: Optional[str],
    auth_token: Optional[str],
) -> Optional[str]:
    """
    Resolve the effective user_id for pattern history and human-gate pause checks.

    In production mode (FHIR_TRUST_CLIENT_USER_ID=false), client_user_id is ignored
    and identity is derived from the runtime bearer token when present.
    """
    if trust_client_user_id():
        return client_user_id

    if auth_token:
        digest = hashlib.sha256(auth_token.encode()).hexdigest()[:16]
        return f"token:{digest}"

    return None