import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SourceType, RecordFilters } from '../types'
import { SourceTabs } from '../components/review/SourceTabs'
import { FilterBar } from '../components/review/FilterBar'
import { RecordTable } from '../components/review/RecordTable'

function deriveSource(tab: string | null, type: string | null): SourceType {
  if (tab === 'travel') {
    if (type === 'hotel')  return 'travel_hotel'
    if (type === 'ground') return 'travel_ground'
    if (type === 'rail')   return 'travel_rail'
    return 'travel_air'   // default travel sub-tab
  }
  return 'utility_electricity'
}

export function ReviewPage() {
  const [searchParams] = useSearchParams()
  const tab  = searchParams.get('tab')
  const type = searchParams.get('type')

  const activeSource = deriveSource(tab, type)

  // filters holds status/dates only — source is handled by SourceTabs
  const [filters, setFilters] = useState<RecordFilters>({ page: 1 })

  const handleSourceChange = (_source: SourceType) => {
    // Reset to page 1 when tab changes
    setFilters(prev => ({ ...prev, page: 1 }))
  }

  return (
    <div className="space-y-0">
      <h1 className="text-xl font-semibold text-[#111827] mb-4">Review Dashboard</h1>

      <SourceTabs activeSource={activeSource} onChange={handleSourceChange} />

      <div className="space-y-4 pt-4">
        <FilterBar filters={filters} onChange={setFilters} />
        <RecordTable
          activeSource={activeSource}
          filters={filters}
          onFiltersChange={setFilters}
        />
      </div>
    </div>
  )
}
