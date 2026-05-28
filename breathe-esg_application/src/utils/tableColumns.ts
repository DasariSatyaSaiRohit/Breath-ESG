import { EsgRecord } from '../types'
import { convertToDisplayUnit } from './unitConversion'

export interface Column {
  key: string     // "raw_data.{originalKey}" or a fixed field key
  header: string  // display label in table header
}

// Shown when no source filter is active (columns=[])
export const BASE_COLUMNS: Column[] = [
  { key: 'description',      header: 'Description' },
  { key: 'activity_date',    header: 'Date' },
  { key: 'normalized_value', header: 'Consumption' }, // renders "123.45 kWh"
  { key: 'scope',            header: 'Scope' },
  { key: 'status',           header: 'Status' },
  { key: 'flag_reason',      header: 'Flag Reason' },
]

// Always appended after raw_data columns.
// normalized_unit removed — unit is embedded in Consumption cell via getDisplayValue().
export const FIXED_TRAILING_COLUMNS: Column[] = [
  { key: 'normalized_value', header: 'Consumption' }, // renders "123.45 kWh"
  { key: 'scope',            header: 'Scope' },
  { key: 'status',           header: 'Status' },
  { key: 'flag_reason',      header: 'Flag Reason' },
]

export const buildTableColumns = (apiColumns: string[]): Column[] => {
  // apiColumns comes from the API response columns field —
  // sorted alphabetically by backend.
  // If empty (no source filter active), fall back to BASE_COLUMNS.
  if (!apiColumns || apiColumns.length === 0) return BASE_COLUMNS
  return [
    ...apiColumns.map(key => ({ key: `raw_data.${key}`, header: key })),
    ...FIXED_TRAILING_COLUMNS,
  ]
}

export const getCellValue = (record: EsgRecord, key: string): string => {
  // raw_data.{key} → look up in record.raw_data
  if (key.startsWith('raw_data.')) {
    const rawKey = key.replace('raw_data.', '')
    return record.raw_data?.[rawKey] ?? '—'
  }
  // Fixed field → look up directly on record
  const val = record[key as keyof EsgRecord]
  if (val === null || val === undefined) return '—'
  return String(val)
}

// Used in RecordRow for the Consumption column (normalized_value key).
// Converts stored value+unit to display standard (kWh, L, km, kg).
export function getDisplayValue(record: EsgRecord): string {
  const result = convertToDisplayUnit(record.normalized_value, record.normalized_unit)
  if (!result) return '—'
  return `${result.displayValue} ${result.displayUnit}`
}
