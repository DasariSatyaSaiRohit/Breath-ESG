import React from 'react'
import { useSearchParams } from 'react-router-dom'
import { UtilityTab } from '../components/ingestion/UtilityTab'
import { TravelTab } from '../components/ingestion/TravelTab'

export function IngestPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') ?? 'utility'

  const setTab = (t: string) => {
    setSearchParams(prev => { prev.set('tab', t); return prev })
  }

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-semibold text-[#111827]">Ingest Data</h1>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-[#F3F4F6] p-1 rounded-lg w-fit">
        {[
          { id: 'utility', label: 'Utility Electricity' },
          { id: 'travel', label: 'Corporate Travel' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-1.5 rounded-md text-sm font-medium transition-colors
              ${tab === t.id ? 'bg-white shadow-sm text-[#111827]' : 'text-[#6B7280] hover:text-[#374151]'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="bg-white border border-[#E5E7EB] rounded-lg p-6 shadow-sm">
        {tab === 'utility' ? <UtilityTab /> : <TravelTab />}
      </div>
    </div>
  )
}
