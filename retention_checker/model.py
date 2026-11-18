"""Data model + export loading for the retention audit."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class ExportError(ValueError):
    """Raised when an export file is malformed."""


VALID_RETENTION_DAYS = (30, 60, 90, 120, 150, 180)
DEFAULT_RETENTION_DAYS = 30


@dataclass(frozen=True)
class Log:
    name: str
    retention_days: int | None
    log_type: str  # CUSTOM | SERVICE


@dataclass(frozen=True)
class LogGroup:
    name: str
    tags: dict = field(default_factory=dict)
    logs: tuple = ()

    def is_prod(self) -> bool:
        return str(self.tags.get("tier", "")).strip().lower() == "prod"


def load_export(path: str) -> tuple:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ExportError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("log_groups"), list):
        raise ExportError(f"{path}: top level must be an object with a 'log_groups' list")
    out = []
    for i, g in enumerate(raw["log_groups"]):
        where = f"log_groups[{i}]"
        if "name" not in g:
            raise ExportError(f"{where}: missing required field 'name'")
        logs = []
        for j, l in enumerate(g.get("logs", [])):
            lwhere = f"{where}.logs[{j}]"
            if "name" not in l:
                raise ExportError(f"{lwhere}: missing required field 'name'")
            rd = l.get("retention_days")
            if rd is not None and (not isinstance(rd, int) or isinstance(rd, bool) or rd <= 0):
                raise ExportError(f"{lwhere}: retention_days must be a positive integer or null, got {rd!r}")
            logs.append(Log(name=l["name"], retention_days=rd, log_type=l.get("log_type", "CUSTOM")))
        out.append(LogGroup(name=g["name"], tags=g.get("tags", {}) or {}, logs=tuple(logs)))
    return tuple(out)
