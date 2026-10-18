// Numeric readings (temperatures etc.): parsing what people type and showing
// values the Ukrainian way (decimal comma).

const number = new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 2 })

export function formatNumber(value: number): string {
  return number.format(value)
}

export function formatReading(value: number, unit: string | null): string {
  return unit ? `${formatNumber(value)} ${unit}` : formatNumber(value)
}

/** "0…4 °C", "≤ −18 °C" (max only) or "≥ 2 °C" (min only). */
export function formatRange(min: number | null, max: number | null, unit: string | null): string {
  const suffix = unit ? ` ${unit}` : ''
  if (min !== null && max !== null) return `${formatNumber(min)}…${formatNumber(max)}${suffix}`
  if (max !== null) return `≤ ${formatNumber(max)}${suffix}`
  if (min !== null) return `≥ ${formatNumber(min)}${suffix}`
  return ''
}

/**
 * Accepts "3,5", "3.5", "-18", "−18" (Unicode minus) and spaces. Returns null
 * for anything that is not a number with at most 2 decimals (the server's precision).
 */
export function parseReading(input: string): number | null {
  const normalized = input.trim().replace(/\s/g, '').replace(',', '.').replace(/[−–]/g, '-')
  if (!/^-?\d{1,5}(\.\d{1,2})?$/.test(normalized)) return null
  return Number(normalized)
}

/** Same inclusive rule as the server; the server's verdict always wins. */
export function isWithinRange(value: number, min: number | null, max: number | null): boolean {
  return (min === null || value >= min) && (max === null || value <= max)
}

/** A stored value back into the input's text form, e.g. 3.5 → "3,5". */
export function readingInputText(value: number | null): string {
  return value === null ? '' : String(value).replace('.', ',')
}
