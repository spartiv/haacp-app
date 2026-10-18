// Calendar dates are "YYYY-MM-DD" strings (the API's format), handled in local time.
// Note: the backend decides "today" in the organization's timezone; the device's local
// date is used only to cap navigation, and the server rejects anything in the future.

const LOCALE = 'uk-UA'

const pad = (n: number) => String(n).padStart(2, '0')

export function toIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** A real calendar date in "YYYY-MM-DD" form (rejects e.g. 2026-02-31). */
export function isIsoDate(value: string | null | undefined): value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  return toIsoDate(parseIsoDate(value)) === value
}

export function todayIsoDate(): string {
  return toIsoDate(new Date())
}

function parseIsoDate(iso: string): Date {
  const [year = 1970, month = 1, day = 1] = iso.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function shiftIsoDate(iso: string, days: number): string {
  const date = parseIsoDate(iso)
  date.setDate(date.getDate() + days)
  return toIsoDate(date)
}

export function formatSheetDate(iso: string): { weekday: string; date: string } {
  const date = parseIsoDate(iso)
  return {
    weekday: date.toLocaleDateString(LOCALE, { weekday: 'long' }),
    // uk-UA appends "р." (рік) to the year; the sheet title reads cleaner without it.
    date: date.toLocaleDateString(LOCALE, { day: '2-digit', month: 'short', year: 'numeric' }).replace(/\s*р\.$/, ''),
  }
}

export function formatTime(isoDateTime: string): string {
  return new Date(isoDateTime).toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit' })
}

export function formatTimestamp(isoDateTime: string): string {
  return new Date(isoDateTime).toLocaleString(LOCALE, {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/** Short day for summaries, e.g. "12.10.2026". */
export function formatShortDate(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString(LOCALE, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/** Whole days from `fromIso` to `toIso` (negative when `toIso` is earlier). DST-safe. */
export function daysBetween(fromIso: string, toIso: string): number {
  const from = parseIsoDate(fromIso)
  const to = parseIsoDate(toIso)
  return Math.round((Date.UTC(to.getFullYear(), to.getMonth(), to.getDate()) -
    Date.UTC(from.getFullYear(), from.getMonth(), from.getDate())) / 86_400_000)
}

/** "YYYY-MM" of a date. */
export function toIsoMonth(iso: string): string {
  return iso.slice(0, 7)
}

export function isIsoMonth(value: string | null | undefined): value is string {
  return typeof value === 'string' && /^\d{4}-(0[1-9]|1[0-2])$/.test(value)
}

/** First day of the month, the date the backend files a monthly record under. */
export function monthStart(isoMonth: string): string {
  return `${isoMonth}-01`
}

export function shiftIsoMonth(isoMonth: string, months: number): string {
  const [year = 1970, month = 1] = isoMonth.split('-').map(Number)
  const date = new Date(year, month - 1 + months, 1)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`
}

/** e.g. { month: "жовтень", year: "2026" } (nominative month name). */
export function formatMonth(isoMonth: string): { month: string; year: string } {
  const date = parseIsoDate(monthStart(isoMonth))
  return {
    month: date.toLocaleDateString(LOCALE, { month: 'long' }),
    year: String(date.getFullYear()),
  }
}
