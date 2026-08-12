from __future__ import annotations

from collections.abc import Mapping


def child_env(base: Mapping[str, str], deny: set[str]) -> dict[str, str]:
    return {k: v for k, v in base.items() if k not in deny}


def redact_argv(argv: list[str]) -> list[str]:
    redacted: list[str] = []
    for item in argv:
        low = item.lower()
        if "key=" in low or "token=" in low or "secret=" in low or "password=" in low:
            redacted.append("***")
        else:
            redacted.append(item)
    return redacted
