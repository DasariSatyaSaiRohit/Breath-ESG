import React, { useState } from 'react'
import { AuditFilterBar } from '../components/audit/AuditFilterBar'
import { AuditTable } from '../components/audit/AuditTable'
import { AuditFilters } from '../types'

export function AuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1 })

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-semibold text-[#111827]">Audit Log</h1>
      <AuditFilterBar filters={filters} onChange={setFilters} />
      <AuditTable filters={filters} onFiltersChange={setFilters} />
    </div>
  )
}
