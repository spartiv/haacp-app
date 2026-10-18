# Polton HACCP API — overview for frontend work

Backend: FastAPI + PostgreSQL, JWT auth, multi-tenant (every domain resource is scoped
under `/api/v1/organizations/{organization_id}/...`). Full machine-readable spec is in
`openapi.json` alongside this file — import it into Swagger UI / Postman / an OpenAPI
codegen tool for exact request/response shapes. This file is the human-readable tour.

## Auth model

- `POST /api/v1/auth/signup` — creates a new Organization + the caller as its `owner`,
  returns `{ user, tokens: {access_token, refresh_token}, organization_id }`
- `POST /api/v1/auth/login` — `{ email, password }` → same token shape, `organization_id`
  is `null` here (a user can belong to multiple orgs; login doesn't pick one for you).
  Right after login call `GET /api/v1/me/organizations` → `[{ organization_id, name, role,
  title }]` (active memberships, sorted by name): one → use it, several → let the user
  pick, none → the account has no access.
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

**Per-item control sheet + audit log (new — preferred for web; mobile can migrate)**
The checklist can also be filled one item at a time, with a draft → submitted lifecycle:
- `GET .../controls/{period}/sheet?date=YYYY-MM-DD` — always 200. Every active item with
  `status` = `pending` | `pass` | `deviation`, its `corrective_action`, `checked_by
  {id, full_name}` and `checked_at`. `record_id`/`status` are `null` until the first check.
  Replaces the "404 means not filled" dance of `GET .../current`.
- `POST .../controls/{period}/items/{item_id}/check` — body `{ status: "pass"|"deviation",
  corrective_action?, amendment_reason?, period_date? }`. Creates the day's record as a
  `draft` on first use. Returns the whole updated sheet.
  - `deviation` needs a `corrective_action` (≥3 chars) → else `422 corrective_action_required`
  - once the record is `submitted`, any change needs an `amendment_reason` (≥3 chars) →
    else `422 amendment_reason_required`; the change is logged as `item_amended`
  - re-sending an identical check is a no-op (no audit entry)
- `POST .../control-records/{record_id}/submit` — finalizes. `409 control_record_incomplete`
  if any item is pending (`error.details` lists `{control_checklist_item_id, label}` for each);
  `409 control_record_already_submitted` if done twice.
- `GET .../control-records/{record_id}/audit-events?cursor=&limit=` — append-only log,
  newest first: `event_type` (`item_checked` | `item_amended` | `record_submitted`),
  `previous_status` → `new_status`, `corrective_action`, `amendment_reason`, `actor
  {id, full_name}`, server `created_at`. Page with `next_cursor` (null on the last page).
  The database itself rejects any UPDATE/DELETE of these rows.

*Compatibility:* `PUT .../current` and `PATCH .../control-records/{id}` still work unchanged
(no corrective action required there). They now also write audit events and **auto-submit**
the record; changes they make after submission are logged as amendments with a fixed
"legacy client" reason. **Submitted records can no longer be deleted** (`409
control_record_submitted`) — only drafts can.

**Measured checklist items (temperatures etc.)**
A control checklist item has `item_type`: `bool` (Так/Ні, as before) or `numeric` — a
reading with `unit` (e.g. `°C`) and a safe range `min_value` / `max_value` (inclusive;
either may be `null` = open, e.g. freezer `max_value: -18`). The type is fixed at creation;
label, unit and range can be PATCHed (partial: send only what changes, `null` opens a bound).
Invalid config → `422 invalid_checklist_item_config`.
- Check a numeric item with `POST .../items/{item_id}/check` body `{ value: 3.5 }` (max 2
  decimals). The **server** decides: inside the range → `pass`, outside → `deviation`
  (needs `corrective_action`, same as any deviation). A `status` sent for a numeric item is
  ignored. Missing value → `422 numeric_value_required`; a value on a Yes/No item →
  `422 numeric_value_not_applicable`.
- Sheet items carry `item_type`, `unit`, `min_value`, `max_value`, `value`. Once measured,
  the limits shown are the ones the value **was judged against** — tightening a range later
  never rewrites past verdicts. Audit events carry `numeric_value` and `item_unit`.
- The legacy full-sheet endpoints (`PUT .../current`, `PATCH .../control-records/{id}`)
  only carry Yes/No answers, so they refuse checklists containing numeric items with
  `422 numeric_items_not_supported` — clients must use the per-item check endpoint.

**Team & "performed by" (shared kitchen devices)**
`GET .../members` → `[{ user_id, full_name, role, title, status }]`, active members first,
then removed ones (kept so old records still resolve to a name). Any member can read it.
Item checks, event entries and batches accept an optional `performed_by_user_id`: who
physically did the work when one account is signed in on a shared tablet. It must be an
**active** member (else `422 invalid_performer`) and defaults to the signed-in user. The
signed-in account is always recorded too (`checked_by` / `actor` / `responsible_user_id` /
`signatory_user_id`); responses add `performed_by` (sheet items, audit events) or
`performed_by_user_id` (event entries, batches). Changing only the performer of a check is
a real change and is audit-logged.

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
`filled` is true only for a **submitted** sheet; a draft reports `filled: false` but
still exposes its `has_deviation`, and its attention label says "розпочато, але не подано".

**Setup progress** — `GET /api/v1/organizations/{id}/setup-progress` → `{ completed, total,
steps: [{ key, label, done, count }] }`. Computed live from existing data, in the
recommended order: `daily_checklist`, `monthly_checklist`, `equipment`, `chemicals`,
`medical_checks`, `products`, `team` (needs ≥2 active members), `first_daily_submitted`.
`label` is Ukrainian; `key` is stable for client-side translations.

## Attachments (shared across Equipment/Chemicals — more domains may adopt it later)
1. `POST /api/v1/organizations/{id}/attachments` — multipart `file` upload (PDF/PNG/JPEG
   only, ≤20MB) → returns `{ id, filename, content_type, size_bytes, ... }`
2. Link it to the owning resource, e.g.
   `POST /api/v1/organizations/{id}/equipment/{equipment_id}/attachment` with
   `{ "attachment_id": "..." }` (also available for chemicals)
3. `GET /api/v1/organizations/{id}/attachments/{attachment_id}` streams the file back
   (sets `Content-Disposition` with the original filename)
4. `DELETE .../equipment/{id}/attachment` detaches *and* deletes the stored file

Storage: S3 in every environment except `HACCP_ENVIRONMENT=development` (the default),
which saves to the git-ignored `uploads/` folder so local uploads work without cloud
credentials. Override with `HACCP_STORAGE_BACKEND=s3|local`. Downloads send the original
filename (Ukrainian included) via RFC 5987 `filename*`.

## Full endpoint list (as of now)

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/health` | no auth |
| POST | `/api/v1/auth/signup` | |
| POST | `/api/v1/auth/login` | |
| POST | `/api/v1/auth/refresh` | |
| POST | `/api/v1/auth/logout` | |
| GET | `/api/v1/me/organizations` | any signed-in user |
| GET | `/api/v1/organizations/{id}/members` | any member |
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
| GET, PATCH, DELETE | `/api/v1/organizations/{id}/control-records/{record_id}` | any member (DELETE: drafts only) |
| GET | `/api/v1/organizations/{id}/control-records/{record_id}/history` | any member |
| GET | `/api/v1/organizations/{id}/controls/{period}/sheet` | any member |
| POST | `/api/v1/organizations/{id}/controls/{period}/items/{item_id}/check` | any member |
| POST | `/api/v1/organizations/{id}/control-records/{record_id}/submit` | any member |
| GET | `/api/v1/organizations/{id}/control-records/{record_id}/audit-events` | any member |
| GET | `/api/v1/organizations/{id}/dashboard` | any member |
| GET | `/api/v1/organizations/{id}/setup-progress` | any member |

`{period}` above is a path segment, literally `daily` or `monthly`.

## Not built — don't design screens around these
- **Traceability / Suppliers / Recalls** — explicitly deferred, not in scope currently
- **Instructions** (SOP documents, read-tracking) — explicitly deferred
- **Tasks** (simple to-do list) — not started

Everything else from the design mockup (auth, dashboard, daily/monthly controls, batch
recording, event logs, directories, equipment, allergens) is live and tested.
