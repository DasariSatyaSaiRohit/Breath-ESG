import React, { useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { UtilityTab } from '../components/ingestion/UtilityTab'
import { TravelTab } from '../components/ingestion/TravelTab'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useToast } from '../hooks/useToast'
import { uploadSapCsv } from '../api/ingestion'

// ── SAP Upload card ─────────────────────────────────────────────────────────
function SapTab() {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [fileName,  setFileName]  = useState<string | null>(null)
  const { addToast } = useToast()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setFileName(file.name)
  }

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file) { addToast('error', 'Please select a CSV file first'); return }
    if (!file.name.endsWith('.csv')) { addToast('error', 'Only .csv files are accepted'); return }

    setUploading(true)
    try {
      const job = await uploadSapCsv(file)
      addToast('success', `SAP ingestion started — Job ${job.job_id} (${job.records_total ?? 0} rows)`)
      setFileName(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err: any) {
      addToast('error', err?.response?.data?.error ?? 'SAP upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-[#6B7280]">
        Upload SAP material movement or purchase order CSV export.
        Only <code className="font-mono bg-[#F3F4F6] px-1 rounded">.csv</code> files are accepted.
      </p>

      {/* File picker — matches existing CSVDropzone visual style */}
      <div
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-[#D1D5DB] rounded-lg p-10 text-center cursor-pointer
          hover:border-[#16A34A] hover:bg-[#F0FDF4] transition-colors bg-white"
      >
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
        />
        <svg className="h-10 w-10 mx-auto mb-3 text-[#9CA3AF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        <p className="text-sm font-medium text-[#374151]">
          {fileName ? fileName : 'Click to select a SAP CSV file'}
        </p>
        {!fileName && (
          <p className="mt-1.5 text-[13px] text-[#6B7280]">
            Accepts SAP MM / FI CSV exports. Max 50 MB.
          </p>
        )}
      </div>

      <Button
        variant="primary"
        onClick={handleUpload}
        loading={uploading}
        disabled={!fileName}
      >
        Upload CSV
      </Button>
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'utility', label: 'Utility Electricity' },
  { id: 'travel',  label: 'Corporate Travel'    },
  { id: 'sap',     label: 'SAP Procurement'     },
]

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
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-1.5 rounded-md text-sm font-medium transition-colors
              ${tab === t.id
                ? 'bg-white shadow-sm text-[#111827]'
                : 'text-[#6B7280] hover:text-[#374151]'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="bg-white border border-[#E5E7EB] rounded-lg p-6 shadow-sm">
        {tab === 'utility' && <UtilityTab />}
        {tab === 'travel'  && <TravelTab />}
        {tab === 'sap'     && <SapTab />}
      </div>
    </div>
  )
}
