"""LOG001-LOG004 rules, grounded in the OCI Logging retention docs."""

from __future__ import annotations

from dataclasses import dataclass

from .model import DEFAULT_RETENTION_DAYS, VALID_RETENTION_DAYS


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    log: str
    detail: str


def _iter_logs(groups: tuple):
    for g in groups:
        for l in g.logs:
            yield g, l


def rule_prod_min_retention(groups: tuple) -> list:
    """LOG001 HIGH: prod-tier log at the 30-day minimum/default."""
    return [
        Finding("LOG001", "HIGH", f"{g.name}/{l.name}",
                f"prod-tier log retains only {DEFAULT_RETENTION_DAYS} days (the service minimum); "
                f"confirm this meets the audit expectation for production")
        for g, l in _iter_logs(groups)
        if g.is_prod() and l.retention_days == DEFAULT_RETENTION_DAYS
    ]


def rule_invalid_retention(groups: tuple) -> list:
    """LOG002 MEDIUM: retention outside the 30-180 ladder (service rejects it at apply time)."""
    return [
        Finding("LOG002", "MEDIUM", f"{g.name}/{l.name}",
                f"retention_days={l.retention_days} is not one of {list(VALID_RETENTION_DAYS)}; "
                f"the service only accepts 30-day increments from 30 to 180")
        for g, l in _iter_logs(groups)
        if l.retention_days is not None and l.retention_days not in VALID_RETENTION_DAYS
    ]


def rule_unset_retention(groups: tuple) -> list:
    """LOG003 MEDIUM: retention unset, so the 30-day default applies."""
    return [
        Finding("LOG003", "MEDIUM", f"{g.name}/{l.name}",
                f"no retention_days set; the service default of {DEFAULT_RETENTION_DAYS} days applies, "
                f"which is easy to assume is longer")
        for g, l in _iter_logs(groups) if l.retention_days is None
    ]


def rule_empty_group(groups: tuple) -> list:
    """LOG004 LOW: log group with zero logs."""
    return [
        Finding("LOG004", "LOW", g.name,
                "log group contains zero logs; an empty container retains nothing")
        for g in groups if not g.logs
    ]


ALL_RULES = (
    rule_prod_min_retention,
    rule_invalid_retention,
    rule_unset_retention,
    rule_empty_group,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(groups: tuple) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(groups))
    findings.sort(key=lambda x: (_SEVERITY_RANK[x.severity], x.rule, x.log))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
