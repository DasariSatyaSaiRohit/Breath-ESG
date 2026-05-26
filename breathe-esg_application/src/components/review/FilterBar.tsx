import React, { useState } from 'react'
import { RecordFilters, RecordStatus } from '../../types'
import { Button } from '../ui/Button'

interface FilterBarProps {
  filters: RecordFilters
  onChange: (filters: RecordFilters) => void
}

export function FilterBar({ filters, onChange }: FilterBarProps) {
  const [local, setLocal] = useState<RecordFilters>(filters)

  const apply = () => onChange({ ...local, page: 1 })

  const selectClass = `rounded-md border border-[#D1D5DB] px-3 py-2 text-sm text-[#374151] bg-white
    focus:outline-none focus:border-[#16A34A] focus:ring-1 focus:ring-[#16A34A]`

  return (
    <div className="flex items-end gap-3 flex-wrap bg-white border border-[#E5E7EB] rounded-lg p-4">
      {/* Source dropdown removed — filtering handled by SourceTabs */}

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-[#6B7280]">Status</label>
        <select
          value={local.status ?? ''}
          onChange={e =>
            setLocal(p => ({ ...p, status: e.target.value as RecordStatus | '' }))
          }
          className={selectClass}
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="flagged">Flagged</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-[#6B7280]">Date From</label>
        <input
          type="date"
          value={local.date_from ?? ''}
          onChange={e => setLocal(p => ({ ...p, date_from: e.target.value }))}
          className={selectClass}
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-[#6B7280]">Date To</label>
        <input
          type="date"
          value={local.date_to ?? ''}
          onChange={e => setLocal(p => ({ ...p, date_to: e.target.value }))}
          className={selectClass}
        />
      </div>

      <Button variant="primary" onClick={apply}>
        Apply Filters
      </Button>
    </div>
  )
}
