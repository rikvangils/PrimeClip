# Story E1-S3 — Add Rights and Compliance Gate

## Status: Done

## Story

As the operator,
I want publish-blocking compliance checks,
so that clips cannot be scheduled without required rights and fan-account safeguards.

## Acceptance Criteria

- [x] Rights status exists per source/clip.
- [x] Missing rights status blocks scheduling.
- [x] Fan-account disclosure metadata is required before publish.
- [x] Compliance decisions are auditable.

## Implementation

### Files Created / Modified

| File | Change |
|------|--------|
| `src/app/db/models.py` | Added `fan_account_disclosed: bool` column to `ComplianceAudit` |
| `src/app/review/compliance.py` | **New** — `get_clip_compliance`, `set_clip_compliance`, `assert_clip_compliant` |
| `src/app/review/schemas.py` | Added `ComplianceSetRequest`, `ComplianceAuditResponse` |
| `src/app/review/api.py` | Added `GET /review/clips/{id}/compliance`, `POST /review/clips/{id}/compliance` |
| `src/app/review/publishing.py` | `schedule_clip_for_distribution` now calls `assert_clip_compliant` gate |
| `alembic/versions/002_add_fan_account_disclosed.py` | **New** — Alembic migration adding `fan_account_disclosed` column |
| `tests/test_compliance_logic.py` | **New** — 18 tests covering service logic and API endpoints |
| `tests/test_publishing_trendpacks_logic.py` | Patched two scheduling success tests to bypass compliance gate |

### API Surface

```
GET  /review/clips/{rendered_clip_id}/compliance
     → 200 ComplianceAuditResponse | 404 if no record

POST /review/clips/{rendered_clip_id}/compliance
     body: { rights_status, decision_reason?, reviewer_id?, fan_account_disclosed }
     → 200 ComplianceAuditResponse | 404 clip not found | 422 invalid rights_status
```

### Compliance Gate Logic (`src/app/review/compliance.py`)

```
assert_clip_compliant(db, rendered_clip_id):
  audit = get_clip_compliance(db, rendered_clip_id)
  if audit is None or audit.rights_status != approved:
    raise ValueError("rights status must be approved")
  if not audit.fan_account_disclosed:
    raise ValueError("fan-account disclosure required")
```

The gate is enforced inside `schedule_clip_for_distribution` in `publishing.py`,
after the `review_status == approved` and `render_path` checks.

### Database

`ComplianceAudit` table has:
- `rights_status` — enum: unknown / pending / approved / rejected
- `decision_reason` — text, auditable notes from reviewer
- `reviewer_id` — identity of decision-maker
- `fan_account_disclosed` — boolean, must be `true` to allow scheduling
- `created_at` — immutable audit timestamp

Migration `002_add_fan_account_disclosed.py` adds the new column with `server_default=false`.

## Test Results

- **18 new tests** in `test_compliance_logic.py` — all passing
- **252 total tests** — 0 failures
- `src/app/review/compliance.py` — **100% coverage**
- `src/app/review/publishing.py` — **100% coverage**
- `src/app/review/api.py` — **100% coverage**

## Delivered

- Rights and compliance gate fully operational
- Immutable audit trail via `ComplianceAudit` table
- Fan-account disclosure required at scheduling time
- All acceptance criteria satisfied
