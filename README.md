# oci-ootb-logging-retention-check

**Category: built-in OCI services project (OOTB).** The custom portfolio project in this pair
is `oci-mfa-coverage-audit`.

## Which built-in OCI services this wires

- **OCI Logging log groups** (`oci_logging_log_group`): the containers that organize logs.
- **OCI Logging logs** (`oci_logging_log` with `retention_duration`): each log's retention is
  a built-in service setting in **30-day increments from 30 to 180 days**; the console default
  for a new log is 30 days, and logs stop being searchable once their retention passes.
  Shortening a log's retention immediately removes access to entries older than the new value.

## Custom code vs native config

- **Native config**: `terraform/` declares a log group and a custom log with an explicit
  180-day `retention_duration` - only built-in provider resources. **Template only - NOT
  plan/apply validated** (no live tenancy).
- **Custom code**: `retention_checker/` audits an offline JSON export of intended/existing
  log configuration against four traps the service accepts silently.

## The rules

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| LOG001 | HIGH | A log in a `tier=prod` log group retains only 30 days (the minimum and the console default) - worth confirming this actually meets the audit/compliance expectation for production. |
| LOG002 | MEDIUM | A log's `retention_days` is outside 30-180 or not a multiple of 30 - the service rejects anything outside the 30/60/90/120/150/180 ladder, so the export/config would fail at apply time. |
| LOG003 | MEDIUM | A log has no `retention_days` set at all - the service default of 30 days applies, which many people assume is longer. |
| LOG004 | LOW | A log group contains zero logs - an empty container retains nothing. |

Exit code: `2` on any HIGH, `1` on MEDIUM/LOW only, `0` when clean.

## Run it

```bash
python -m retention_checker.cli samples/logs_messy.json   # exits 2, all 4 rules fire
python -m retention_checker.cli samples/logs_clean.json   # exits 0
python -m unittest discover -s tests -v                   # 18 tests, stdlib only
```

## Honest limits

- **Offline audit**: the JSON export is synthetic; nothing calls the OCI Logging API.
- Rule semantics are grounded in the official docs as of Nov 2026
  (<https://docs.oracle.com/en-us/iaas/Content/Logging/Task/enabling_logging.htm>):
  retention in 30-day increments, 30-180 days, 30-day console default, entries become
  unavailable once retention passes, and shortening retention removes older entries
  immediately.
- Findings describe what the export records; a 30-day prod retention is a review flag, not
  proof of a compliance breach - the right window depends on your obligations.
- The `tier=prod` tag is this tool's convention, not an OCI standard.
- Terraform template is illustrative and has **not** been plan/apply validated.

## Project status

Built as a daily OOTB project. 18 unit tests, green locally and in CI. Free tier only; no
live cloud calls, no spend.
