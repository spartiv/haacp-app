# Polton HACCP API — overview for frontend work

Backend: FastAPI + PostgreSQL, JWT auth, multi-tenant (every domain resource is scoped
under `/api/v1/organizations/{organization_id}/...`). Full machine-readable spec is in
`openapi.json` alongside this file — import it into Swagger UI / Postman / an OpenAPI
codegen tool for exact request/response shapes. This file is the human-readable tour.

## Auth model

- `POST /api/v1/auth/signup` — creates a new Organization + the caller as its `owner`,
  returns `{ user, tokens: {access_token, refresh_token}, organization_id }`
- `POST /api/v1/auth/login` — `{ email, password }` → same token shape, `organization_id`
  is `null` here (a user can belong to multiple orgs; login doesn't pick one for you —
  there's no "list my orgs" endpoint yet, so today a client should just remember the
  `organization_id` it got at signup/invite-accept time)
- `POST /api/v1/auth/refresh` — rotates a refresh token for a new pair (old one becomes invalid)
- `POST /api/v1/auth/logout` — revokes a refresh token
- All other endpoints require `Authorization: Bearer <access_token>`
- Access tokens expire in 15 min, refresh tokens in 30 days (configurable server-side)

### Team invites (no self-serve "join" — invite-only)
- `POST /api/v1/organizations/{id}/invites` — owner/manager only, body `{ email, role }`
  (`role` is `owner` | `manager` | `staff`); this "sends" an email (stubbed — logs only
  right now, no real email provider wired up yet) containing an accept link/token
- `GET /api/v1/invites/{token}` — public, preview who/what org/what role before accepting
- `POST /api/v1/invites/{token}/accept` — body `{ password, full_name }` if the invited
  email has no account yet (creates one); if it already has an account, call this
  **while authenticated** as that user with an empty body instead

## Roles & permissions (applies across every domain resource)
- **owner / manager**: create/edit/delete configuration-ish things (products, checklists,
  equipment, directory entries, invites)
- **staff**: can do all of the above *except* org configuration — but can freely record
  day-to-day data (batches, control records, event log entries) since that's the actual
  shop-floor job
- A 403 with `{"error": {"code": "forbidden", ...}}` means either not a member of that
  org, or wrong role for that action

## Error envelope (every non-2xx response)
```json
{ "error": { "code": "some_snake_case_code", "message": "human readable" } }
```
422 validation errors additionally include `"details": [...]` (Pydantic's per-field errors).

## Domain model & key business rules

**Product → ChecklistItem → Batch → BatchAnswer**
A product owns a reusable checklist (a list of Yes/No questions). Recording a batch
(партія) means answering every current checklist question for that product, plus a lot
number, optional name, and production date. **"No" always means deviation** — the
backend computes `has_deviation` server-side, the client never sets it. Editing a batch
snapshots its prior state to history first (`GET .../batches/{id}/history`), so nothing
is ever silently lost — batches are never hard-deleted either, just soft-deleted.

**Daily/monthly Controls (ControlChecklistItem → ControlRecord → ControlAnswer)**
Same Yes/No + "No means deviation" mechanics as batches, but facility-wide instead of
per-product — e.g. "is water quality OK today," "was pest control done this month."
Two independent checklists (`period` = `daily` or `monthly`), each configured separately.
The key endpoint is the **upsert**: `PUT .../controls/{period}/current` fills in
*today's* (or *this month's*) record if it doesn't exist yet, or edits it (snapshotting
the prior state to history) if it does — there's at most one live record per calendar
day/month per org, computed in **the organization's own timezone**, not the device's or
server's. `GET .../controls/{period}/current` 404s with code `control_record_not_filled`
if nothing's been recorded yet for the current period — use that to decide whether to
show a blank form or a pre-filled one. Past records can also be viewed/edited/deleted
directly via `/control-records/{id}...` (no 24h lock — always editable, always
audit-trailed via history).

*Backfilling a specific date:* the upsert body now takes an optional `period_date`
(`"YYYY-MM-DD"`). Omit it and it defaults to today/this-month, same as before. Pass a
past date to fill in (or edit — same upsert-by-date semantics) a control for that day
instead of today; for `monthly`, any day within the target month works and is normalized
server-side to that month's 1st. **Future dates are rejected** with `422` /
`{"error": {"code": "future_period_date", ...}}` — the UI should disable/hide future
dates in whatever date picker it uses (e.g. cap a native date picker's max at today, in
the org's timezone if you have it, otherwise device-local is a reasonable approximation).
`GET .../controls/{period}/records` (the history-by-date list) already returns every
past record with its `period_date`, so a "Daily Control" screen can render a
date-indexed history without any new endpoint — the only actual gap this closed was the
ability to *submit* for a day other than today.

Both the upsert body and every `ControlRecordResponse` also now carry an optional
free-text `note` (`string | null`) — a general remark field alongside the Yes/No
answers, not tied to any specific checklist item. `null`/omitted means "no note."

**Equipment**
`type` (`production`|`refrigeration`|`measuring`|`other`), maintenance `frequency` (free
text), `amount`, `affects_product_safety` (bool — feeds the dashboard's attention list),
and an optional attached document (passport/manual).

**Directories** — `chemicals` (name + category `cleaning`|`disinfecting` + optional SDS
attachment), `waste-types` (name + disposal method), `medical-checks` (employee name as
free text — not linked to a real account — + next checkup date, also feeds the dashboard).

**Allergens** — the fixed 14-item EU/UA legal allergen list. Read-only catalog, seeded
once; per-org you can only toggle `present: true/false` on each, never add/remove/rename.

**Event logs** — 9 fixed categories (glass breakage, water tests, filter changes,
equipment maintenance, visitor log, disinfection, pest control, deratization, chemical
briefings). `GET .../event-log-types` to get the catalog + each type's `log_schema`
(`standard`|`water`|`pests`), which determines what `payload` shape that entry needs:
- `standard`: `{ "details": "free text" }` — never a deviation
- `water`: `{ "params": ["pH", "Хлор", ...], "result": "ok"|"deviation" }` — deviation
  iff `result == "deviation"`. `params` must be from the fixed set: pH, Хлор, Мутність,
  Мікробіологія, Твердість.
- `pests`: `{ "detected": "yes"|"no", "actions": "free text" }` — deviation iff detected

**Dashboard** — `GET /api/v1/organizations/{id}/dashboard`, one call, no params. Returns:
```json
{
  "daily_control": { "filled": true, "has_deviation": false },
  "monthly_control": { "filled": false, "has_deviation": null },
  "batches_this_month": 4,
  "attention_items": [
    { "label": "...", "severity": "critical"|"warning"|"info", "days": -1 }
  ]
}
```
`attention_items` is pre-sorted (critical first, then by urgency) — render top to bottom,
don't re-sort client-side. Currently draws from: unfilled daily/monthly controls
(critical), safety-critical equipment missing a document (warning), medical checkups
overdue or due within 14 days (critical/warning). `days` is negative when overdue.

## Attachments (shared across Equipment/Chemicals — more domains may adopt it later)
1. `POST /api/v1/organizations/{id}/attachments` — multipart `file` upload (PDF/PNG/JPEG
   only, ≤20MB) → returns `{ id, filename, content_type, size_bytes, ... }`
2. Link it to the owning resource, e.g.
   `POST /api/v1/organizations/{id}/equipment/{equipment_id}/attachment` with
   `{ "attachment_id": "..." }` (also available for chemicals)
3. `GET /api/v1/organizations/{id}/attachments/{attachment_id}` streams the file back
   (sets `Content-Disposition` with the original filename)
4. `DELETE .../equipment/{id}/attachment` detaches *and* deletes the stored file

## Full endpoint list (as of now)

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/health` | no auth |
| POST | `/api/v1/auth/signup` | |
| POST | `/api/v1/auth/login` | |
| POST | `/api/v1/auth/refresh` | |
| POST | `/api/v1/auth/logout` | |
| POST | `/api/v1/organizations/{id}/invites` | owner/manager |
| GET | `/api/v1/invites/{token}` | public |
| POST | `/api/v1/invites/{token}/accept` | |
| POST, GET | `/api/v1/organizations/{id}/products` | create: owner/manager |
| GET, DELETE | `/api/v1/organizations/{id}/products/{product_id}` | delete: owner/manager |
| GET, POST | `/api/v1/organizations/{id}/products/{product_id}/checklist-items` | POST: owner/manager |
| PATCH, DELETE | `/api/v1/organizations/{id}/products/{product_id}/checklist-items/{item_id}` | owner/manager |
| POST, GET | `/api/v1/organizations/{id}/products/{product_id}/batches` | any member |
| GET, PATCH, DELETE | `/api/v1/organizations/{id}/batches/{batch_id}` | any member |
| GET | `/api/v1/organizations/{id}/batches/{batch_id}/history` | any member |
| POST | `/api/v1/organizations/{id}/attachments` | any member |
| GET | `/api/v1/organizations/{id}/attachments/{attachment_id}` | any member |
| POST, GET | `/api/v1/organizations/{id}/equipment` | POST: owner/manager |
| GET, PATCH, DELETE | `/api/v1/organizations/{id}/equipment/{equipment_id}` | mutate: owner/manager |
| POST, DELETE | `/api/v1/organizations/{id}/equipment/{equipment_id}/attachment` | owner/manager |
| POST, GET | `/api/v1/organizations/{id}/chemicals` | POST: owner/manager |
| PATCH, DELETE | `/api/v1/organizations/{id}/chemicals/{chemical_id}` | owner/manager |
| POST, DELETE | `/api/v1/organizations/{id}/chemicals/{chemical_id}/attachment` | owner/manager |
| POST, GET | `/api/v1/organizations/{id}/waste-types` | POST: owner/manager |
| PATCH, DELETE | `/api/v1/organizations/{id}/waste-types/{waste_type_id}` | owner/manager |
| POST, GET | `/api/v1/organizations/{id}/medical-checks` | POST: owner/manager |
| PATCH, DELETE | `/api/v1/organizations/{id}/medical-checks/{medical_check_id}` | owner/manager |
| GET | `/api/v1/organizations/{id}/allergens` | any member |
| PATCH | `/api/v1/organizations/{id}/allergens/{allergen_id}` | owner/manager |
| GET | `/api/v1/organizations/{id}/event-log-types` | any member |
| POST, GET | `/api/v1/organizations/{id}/event-log-types/{type_id}/entries` | any member |
| DELETE | `/api/v1/organizations/{id}/event-entries/{entry_id}` | any member |
| GET, POST | `/api/v1/organizations/{id}/controls/{period}/checklist-items` | POST: owner/manager |
| PATCH, DELETE | `/api/v1/organizations/{id}/controls/{period}/checklist-items/{item_id}` | owner/manager |
| GET, PUT | `/api/v1/organizations/{id}/controls/{period}/current` | any member |
| GET | `/api/v1/organizations/{id}/controls/{period}/records` | any member |
| GET, PATCH, DELETE | `/api/v1/organizations/{id}/control-records/{record_id}` | any member |
| GET | `/api/v1/organizations/{id}/control-records/{record_id}/history` | any member |
| GET | `/api/v1/organizations/{id}/dashboard` | any member |

`{period}` above is a path segment, literally `daily` or `monthly`.

## Not built — don't design screens around these
- **Traceability / Suppliers / Recalls** — explicitly deferred, not in scope currently
- **Instructions** (SOP documents, read-tracking) — explicitly deferred
- **Tasks** (simple to-do list) — not started
- No "list my organizations" endpoint yet (relevant if a user is ever in >1 org)

Everything else from the design mockup (auth, dashboard, daily/monthly controls, batch
recording, event logs, directories, equipment, allergens) is live and tested.
