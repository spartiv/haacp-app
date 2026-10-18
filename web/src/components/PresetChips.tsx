import { CORRECTIVE_ACTION_PRESETS, uk } from '../i18n/uk'
import './PresetChips.css'

/** Adds a preset as its own sentence; the text stays editable. */
function appendPreset(current: string, preset: string): string {
  const trimmed = current.trimEnd()
  if (trimmed === '') return preset
  return /[.!?]$/.test(trimmed) ? `${trimmed} ${preset}` : `${trimmed}. ${preset}`
}

/** Quick corrective-action chips under a text field: tap to append, dashed = available, solid = added. */
export function PresetChips({ value, onChange }: { value: string; onChange: (next: string) => void }) {
  return (
    <div className="preset-chips" role="group" aria-label={uk.controls.presets}>
      {CORRECTIVE_ACTION_PRESETS.map((preset) => {
        const used = value.includes(preset)
        return (
          <button
            key={preset}
            type="button"
            className={`preset-chip${used ? ' preset-chip--used' : ''}`}
            aria-pressed={used}
            disabled={used}
            onClick={() => onChange(appendPreset(value, preset))}
          >
            {used ? '✓ ' : '+ '}
            {preset}
          </button>
        )
      })}
    </div>
  )
}
