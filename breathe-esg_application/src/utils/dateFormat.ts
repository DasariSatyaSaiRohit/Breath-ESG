// date-fns-tz is used for timezone-aware formatting.
// If not installed: npm install date-fns date-fns-tz
// Falls back gracefully if the library is unavailable at runtime.

let formatFn: ((date: Date, fmt: string, opts: { timeZone: string }) => string) | null = null
let toZonedTimeFn: ((date: Date, tz: string) => Date) | null = null

// Lazy import — avoids hard crash if date-fns-tz is not yet installed
async function loadDateFns() {
  try {
    const mod = await import('date-fns-tz')
    formatFn = mod.format
    toZonedTimeFn = mod.toZonedTime ?? (mod as any).utcToZonedTime
  } catch {
    // library not available — fallback mode
  }
}

loadDateFns()

// Converts tenant format tokens to date-fns pattern tokens
function toDateFnsPattern(tenantFormat: string): string {
  return tenantFormat
    .replace(/DD/g, 'dd')
    .replace(/YYYY/g, 'yyyy')
    .replace(/YY/g, 'yy')
  // MM is already correct for date-fns
}

export function formatActivityDate(
  utcIso: string,
  timezone: string,
  dateDisplayFormat: string
): string {
  if (!utcIso) return '—'

  // If date-fns-tz is loaded, use it for proper timezone conversion
  if (formatFn && toZonedTimeFn) {
    try {
      const zoned = toZonedTimeFn(new Date(utcIso), timezone)
      return formatFn(zoned, toDateFnsPattern(dateDisplayFormat), { timeZone: timezone })
    } catch {
      // fall through to basic fallback
    }
  }

  // Fallback: basic formatting without timezone library
  try {
    const d = new Date(utcIso)
    if (isNaN(d.getTime())) return utcIso
    const day   = String(d.getUTCDate()).padStart(2, '0')
    const month = String(d.getUTCMonth() + 1).padStart(2, '0')
    const year  = String(d.getUTCFullYear())
    return dateDisplayFormat
      .replace('DD', day)
      .replace('MM', month)
      .replace('YYYY', year)
      .replace('YY', year.slice(2))
  } catch {
    return utcIso
  }
}

// Shorter version for timestamps (audit log etc.) — always shows date + time
export function formatTimestamp(utcIso: string, timezone = 'UTC'): string {
  if (!utcIso) return '—'
  try {
    const d = new Date(utcIso)
    return d.toLocaleDateString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      timeZone: timezone,
    }) + ', ' + d.toLocaleTimeString('en-GB', {
      hour: '2-digit', minute: '2-digit',
      timeZone: timezone,
    })
  } catch {
    return utcIso
  }
}
