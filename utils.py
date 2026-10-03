import re

_SENSITIVE_PATTERNS = [
    re.compile(r'(token["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(app_password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'(bot_token["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE),
]


def mask_sensitive_data(text: str) -> str:
    if not text:
        return text
    masked = text
    for pattern in _SENSITIVE_PATTERNS:
        masked = pattern.sub(r"\1***MASKED***", masked)
    return masked


def compute_backoff_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    attempt = max(attempt, 0)
    delay = base_delay * (2 ** attempt)
    delay = min(delay, max_delay)
    return delay
