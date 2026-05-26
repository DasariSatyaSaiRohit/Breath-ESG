import React, { useState } from 'react'
import { AuditFilters, AuditAction } from '../../types'
import { Button } from '../ui/Button'

interface AuditFilterBarProps {
  filters: AuditFilters
  onChange: (f: AuditFilters) => void
}

export function AuditFilterBar({ filters, onChange }: AuditFilterBarProps) {
  const [local, setLocal] = useState<AuditFilters>(filters)

  const selectClass = `rounded-md border border-[#D1D5DB] px-3 py-2 text-sm text-[#374151] bg-white
    focus:outline-none focus:border-[#16A34A] focus:ring-1 focus:ring-[#16A34A]`

  return (
    <div className="flex items-end gap-3 flex-wrap bg-white border border-[#E5E7EB] rounded-lg p-4">
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

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-[#6B7280]">Action</label>
        <select
          value={local.action ?? ''}
          onChange={e => setLocal(p => ({ ...p, action: e.target.value as AuditAction | '' }))}
          className={selectClass}
        >
          <option value="">All Actions</option>
          <option value="created">Created</option>
          <option value="edited">Edited</option>
          <option value="approved">Approved</option>
          <option value="flagged">Flagged</option>
          <option value="bulk_approved">Bulk Approved</option>
        </select>
      </div>

      <Button variant="primary" onClick={() => onChange({ ...local, page: 1 })}>Apply</Button>
    </div>
  )
}
