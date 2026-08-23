import re
from typing import Any


VALID_ROLES = {"customer", "support_agent", "ops_manager", "admin"}
INTERNAL_ROLES = {"support_agent", "ops_manager", "admin"}
MANAGER_ROLES = {"ops_manager", "admin"}


class SecurityError(Exception):
    pass


def normalize_role(role: str | None) -> str:
    normalized = (role or "customer").strip().lower()
    if normalized not in VALID_ROLES:
        raise SecurityError(f"Unknown or unsupported role '{role}'.")
    return normalized


def is_internal_role(role: str | None) -> bool:
    return normalize_role(role) in INTERNAL_ROLES


SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_ -]?key|secret|token|password)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{12,})['\"]?"),
    re.compile(r"\b(sk|pk|ghp|xox[baprs])-[A-Za-z0-9_\-]{10,}\b"),
    re.compile(r"\b[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}\b"),
]


def redact_sensitive_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    redacted = value
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def redact_sensitive_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: redact_sensitive_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [redact_sensitive_payload(item) for item in payload]
    return redact_sensitive_text(payload)
