// ─── Display standard per quantity type ────────────────────────────────────
// Energy    → kWh
// Volume    → L   (litres)
// Distance  → km
// Mass      → kg
// ───────────────────────────────────────────────────────────────────────────

export type DisplayUnit = 'kWh' | 'L' | 'km' | 'kg' | string

export interface ConversionResult {
  displayValue: string   // formatted to 2 decimal places, e.g. "123.45"
  displayUnit: DisplayUnit
}

const ENERGY_TO_KWH: Record<string, number> = {
  kwh: 1,
  wh: 0.001,
  mwh: 1000,
  gwh: 1_000_000,
}

const VOLUME_TO_L: Record<string, number> = {
  l: 1,
  litre: 1,
  litres: 1,
  ml: 0.001,
  kl: 1000,
  'm3': 1000,
  'm³': 1000,
  gal: 3.78541,
  gallon: 3.78541,
  gallons: 3.78541,
}

const DISTANCE_TO_KM: Record<string, number> = {
  km: 1,
  kilometres: 1,
  kilometers: 1,
  m: 0.001,
  miles: 1.60934,
  mile: 1.60934,
  ft: 0.0003048,
  feet: 0.0003048,
}

const MASS_TO_KG: Record<string, number> = {
  kg: 1,
  g: 0.001,
  t: 1000,
  tonne: 1000,
  tonnes: 1000,
  ton: 1000,
  lbs: 0.453592,
  lb: 0.453592,
}

export function convertToDisplayUnit(
  rawValue: string | null,
  rawUnit: string
): ConversionResult | null {
  // Returns null if rawValue is null/empty or unit is unrecognised —
  // caller renders '—' in that case.
  if (!rawValue) return null
  const num = parseFloat(rawValue)
  if (isNaN(num)) return null

  const unit = rawUnit.trim().toLowerCase()

  if (unit in ENERGY_TO_KWH)
    return { displayValue: (num * ENERGY_TO_KWH[unit]).toFixed(2), displayUnit: 'kWh' }
  if (unit in VOLUME_TO_L)
    return { displayValue: (num * VOLUME_TO_L[unit]).toFixed(2), displayUnit: 'L' }
  if (unit in DISTANCE_TO_KM)
    return { displayValue: (num * DISTANCE_TO_KM[unit]).toFixed(2), displayUnit: 'km' }
  if (unit in MASS_TO_KG)
    return { displayValue: (num * MASS_TO_KG[unit]).toFixed(2), displayUnit: 'kg' }

  // Unknown unit — return as-is so it still renders
  return { displayValue: parseFloat(rawValue).toFixed(2), displayUnit: rawUnit }
}
