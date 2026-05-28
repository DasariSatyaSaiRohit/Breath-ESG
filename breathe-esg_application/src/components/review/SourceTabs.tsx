import React from 'react'
import { useSearchParams } from 'react-router-dom'
import { SourceType } from '../../types'

interface SourceTabsProps {
  activeSource: SourceType
  onChange: (source: SourceType) => void
}

const travelTypes = [
  { type: 'air',    label: 'Air',    source: 'travel_air'    as SourceType },
  { type: 'hotel',  label: 'Hotel',  source: 'travel_hotel'  as SourceType },
  { type: 'ground', label: 'Ground', source: 'travel_ground' as SourceType },
  { type: 'rail',   label: 'Rail',   source: 'travel_rail'   as SourceType },
]

function tabClass(active: boolean, size: 'base' | 'sm' = 'base') {
  const text = size === 'sm' ? 'text-sm' : 'text-sm font-medium'
  return [
    text,
    'pb-2 transition-colors cursor-pointer whitespace-nowrap',
    active
      ? 'border-b-2 border-[#16A34A] text-[#16A34A] font-medium'
      : 'text-[#6B7280] hover:text-[#374151] border-b-2 border-transparent',
  ].join(' ')
}

export function SourceTabs({ activeSource, onChange }: SourceTabsProps) {
  const [, setSearchParams] = useSearchParams()

  const isTravel = activeSource.startsWith('travel_')
  const isSap    = activeSource === 'sap_procurement'
  const isUtility = !isTravel && !isSap

  const handleMainTab = (tab: 'utility' | 'travel' | 'sap') => {
    let source: SourceType
    if (tab === 'utility') {
      source = 'utility_electricity'
      setSearchParams({ tab: 'utility' })
    } else if (tab === 'sap') {
      source = 'sap_procurement'
      setSearchParams({ tab: 'sap' })
    } else {
      source = 'travel_air'
      setSearchParams({ tab: 'travel', type: 'air' })
    }
    onChange(source)
  }

  const handleTravelSubTab = (type: string, source: SourceType) => {
    setSearchParams({ tab: 'travel', type })
    onChange(source)
  }

  return (
    <div>
      {/* Main tab row */}
      <div className="flex gap-6 border-b border-[#E5E7EB]">
        <button
          onClick={() => handleMainTab('utility')}
          className={tabClass(isUtility)}
        >
          Utility Electricity
        </button>
        <button
          onClick={() => handleMainTab('travel')}
          className={tabClass(isTravel)}
        >
          Corporate Travel
        </button>
        <button
          onClick={() => handleMainTab('sap')}
          className={tabClass(isSap)}
        >
          SAP Procurement
        </button>
      </div>

      {/* Sub-tab row — only when travel is active; hidden for SAP */}
      {isTravel && (
        <div className="flex gap-4 bg-[#F8F9FA] px-4 py-2 border-b border-[#E5E7EB]">
          {travelTypes.map(({ type, label, source }) => (
            <button
              key={type}
              onClick={() => handleTravelSubTab(type, source)}
              className={tabClass(activeSource === source, 'sm')}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
