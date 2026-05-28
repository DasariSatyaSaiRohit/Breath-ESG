import React from 'react'
import { EsgRecord } from '../../types'
import { Column, getCellValue, getDisplayValue } from '../../utils/tableColumns'
import { formatActivityDate } from '../../utils/dateFormat'
import { Badge } from '../ui/Badge'
import { useAuth } from '../../context/AuthContext'

interface RecordRowProps {
  record: EsgRecord
  columns: Column[]
  selected: boolean
  onSelect: (id: string) => void
  onApprove: (id: string) => void
  onFlag: (id: string) => void
  onEdit: (record: EsgRecord) => void
}

const LockIcon = () => (
  <svg className="h-4 w-4 text-[#9CA3AF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
  </svg>
)

export function RecordRow({ record, columns, selected, onSelect, onApprove, onFlag, onEdit }: RecordRowProps) {
  const { tenantConfig } = useAuth()

  const timezone         = tenantConfig?.timezone          ?? 'UTC'
  const dateDisplayFmt   = tenantConfig?.date_display_format ?? 'YYYY-MM-DD'

  const renderCell = (col: Column) => {
    // Consumption column — convert to display unit (kWh, L, km, kg)
    if (col.key === 'normalized_value') {
      return getDisplayValue(record)
    }

    // Activity date — apply tenant timezone + format
    if (col.key === 'activity_date') {
      return formatActivityDate(record.activity_date, timezone, dateDisplayFmt)
    }

    // Status badge
    if (col.key === 'status') {
      return <Badge variant={record.status}>{record.status}</Badge>
    }

    // Flag reason — truncate with tooltip
    if (col.key === 'flag_reason') {
      const reason = record.flag_reason ?? ''
      const truncated = reason.length > 40 ? reason.slice(0, 40) + '…' : reason
      return <span title={reason}>{truncated || '—'}</span>
    }

    // All other cells (raw_data.* and remaining fixed fields)
    return getCellValue(record, col.key)
  }

  return (
    <tr className="border-b border-[#E5E7EB] hover:bg-[#F9FAFB] transition-colors">
      {/* Checkbox */}
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onSelect(record.id)}
          className="rounded border-[#D1D5DB] text-[#16A34A] focus:ring-[#16A34A]"
        />
      </td>

      {/* Data columns — driven entirely by columns prop */}
      {columns.map(col => (
        <td key={col.key} className="px-4 py-3 text-sm text-[#374151] whitespace-nowrap">
          {renderCell(col)}
        </td>
      ))}

      {/* Actions — always last */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Duplicate badge — E11c */}
          {record.is_duplicate && (
            <span className="bg-[#FEF3C7] text-[#92400E] text-xs px-1.5 py-0.5 rounded font-medium">
              Duplicate
            </span>
          )}

          {record.is_locked ? (
            <LockIcon />
          ) : (
            <>
              {record.status !== 'approved' && (
                <button
                  onClick={() => onApprove(record.id)}
                  className="text-xs px-2 py-1 rounded border border-[#D1D5DB] text-[#374151] hover:bg-[#F9FAFB] transition-colors"
                >
                  Approve
                </button>
              )}
              <button
                onClick={() => onFlag(record.id)}
                className="text-xs px-2 py-1 rounded border border-[#D1D5DB] text-[#374151] hover:bg-[#F9FAFB] transition-colors"
              >
                Flag
              </button>
              <button
                onClick={() => onEdit(record)}
                className="text-[#6B7280] hover:text-[#374151] transition-colors"
                title="Edit"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  )
}
