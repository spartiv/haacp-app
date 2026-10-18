# HACCP Web — Design System

**Concept: Industrial Technical Brutal-Minimalism.**
The interface should read like a laboratory logbook, a stainless-steel equipment
nameplate and a health-inspection form — not a SaaS template. Every rule below is
mandatory for every component.

Visual reference: [`prototypes/ccp-temperature-card.html`](prototypes/ccp-temperature-card.html)
(static mock — the backend has no temperature API; use it for styling only).

---

## 1. Forbidden

- Rounded corners (pill buttons, soft cards), drop shadows, blurs, glassmorphism.
- Gradients used as decoration, pastel palettes.
- "Medical green" for success states.
- Default Tailwind palette colors (`bg-gray-100`, `text-green-600`, …). Use tokens only.
- Status shown by color alone.

## 2. Tokens

Defined once as CSS variables on `:root`. Components never hard-code hex values.

| Token          | Value                | Use                                                    |
| -------------- | -------------------- | ------------------------------------------------------ |
| `--bg`         | `#F2F2F4`            | Page background (matte anodized aluminum)              |
| `--surface`    | `#FFFFFF`            | Cards, sheets, inputs                                  |
| `--ink`        | `#111111`            | Text, borders, **all buttons/actions**                 |
| `--ink-muted`  | `#4A4A4F`            | Secondary metadata (still ≥ 7:1 on white)              |
| `--rule-soft`  | `#B8B8BE`            | Minor dividers, gauge ticks                            |
| `--charcoal`   | `#1C1C1F`            | Dark sub-surfaces (nav, equipment panels)              |
| `--ok`         | `#0049FF`            | **Verified/safe status only.** Never for buttons/links |
| `--crit`       | `#E60000`            | Critical limit breach, warnings                        |
| `--font-mono`  | JetBrains Mono       | Data, readings, IDs, labels, body                      |
| `--font-display` | Space Grotesk      | Large structural titles                                |
| `--track`      | `0.05em`             | Letter-spacing for all uppercase text                  |

## 3. Geometry

- `border-radius: 0` everywhere. Exception: small text inputs may use `2px`.
- No `box-shadow`. Separate elements with `1px solid var(--ink)` borders.
- Dashed/dotted borders = perforation lines of tear-off sheets (row dividers,
  detachable slips such as corrective-action forms).
- Stacked paper: a card may have an offset "sheet behind" (bordered, not shadowed),
  and slips may overlap the card they belong to.

## 4. Typography

- Headers, status labels and IDs: `text-transform: uppercase; letter-spacing: var(--track)`.
- Contrast scale: very large structural titles/readings next to very small, dense
  metadata (10–11px mono). Avoid the comfortable middle.
- Numbers use tabular figures. Use the real minus sign `−` (U+2212) and an explicit
  `+` for positive temperatures.

## 5. Status semantics (accessibility — kitchen glare, color-blind staff)

Status is always communicated **three ways**: text label + border pattern + color.

UI language is Ukrainian. All strings live in `src/i18n/uk.ts` — never hard-code text in components.

| State      | Label               | Border                       | Color    |
| ---------- | ------------------- | ---------------------------- | -------- |
| Verified   | `[ В НОРМІ ]`       | solid                        | `--ok`   |
| Deviation  | `[ ВІДХИЛЕННЯ ]`    | **dashed** 2px               | `--crit` |
| Breach     | `[ CRIT_LIMIT ]`    | **dashed** 2px               | `--crit` |
| Not logged | `[ В ОЧІКУВАННІ ]`  | dotted                       | `--ink`  |

Sheet stamps: `[ НЕ РОЗПОЧАТО ]` dotted, `[ ЧЕРНЕТКА ]` dashed ink, `[ ПОДАНО ]` solid blue rotated.

API mapping: `has_deviation === true` → `[ ВІДХИЛЕННЯ ]`; `false` → `[ В НОРМІ ]`; record not
filled (`control_record_not_filled` / `has_deviation: null`) → `[ В ОЧІКУВАННІ ]`.

Breach zones on gauges/charts additionally use a diagonal hatch pattern.

## 6. Actions

- Primary: solid `--ink` background, white text. Secondary: white with `1px` ink border.
- Minimum touch target **48px** high (staff may wear gloves).
- Labels say exactly what happens: "Log corrective action", not "Submit".
- Focus: `3px solid var(--ink)` outline with offset. Never remove it.

## 7. No reference stamps

Decided 2026-10-18 for the production release: components carry **no** corner ID stamps
(`[ID: …]`, `SYS_REF_…`). The UI stays clean and distraction-free; record identity is shown
only where staff need it (dates, names, status stamps like `[ ПОДАНО ]`).

## 8. Copy

- Plain language for kitchen staff; uppercase is a style, not a tone.
- Errors and breaches state what happened and what to do next, with numbers.
  ("Above the +5.0 °C limit since 12:00. Move stock to FRG-04.")
