import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { TravelPullForm } from './TravelPullForm'
import { CSVDropzone } from './CSVDropzone'
import { CSVPreview } from './CSVPreview'
import { StepIndicator } from '../ui/StepIndicator'
import { JobResult } from './JobResult'
import { Button } from '../ui/Button'
import { useUploadTravelCSV, useJobPolling } from '../../hooks/useIngestion'
import { IngestionJob } from '../../types'

type CSVState = 'idle' | 'preview' | 'uploading' | 'done' | 'failed'

const STEPS = ['Uploading', 'Parsing', 'Normalizing', 'Done']

export function TravelTab() {
  const [searchParams, setSearchParams] = useSearchParams()
  const mode = searchParams.get('mode') ?? 'pull'

  const setMode = (m: string) => {
    setSearchParams(prev => { prev.set('mode', m); return prev })
  }

  // CSV flow state
  const [csvState, setCsvState] = useState<CSVState>('idle')
  const [file, setFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobResult, setJobResult] = useState<IngestionJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [stepIndex, setStepIndex] = useState(0)

  const upload = useUploadTravelCSV()
  const { data: polledJob } = useJobPolling(jobId, csvState === 'uploading')

  React.useEffect(() => {
    if (!polledJob) return
    if (polledJob.status === 'done') { setJobResult(polledJob); setCsvState('done') }
    else if (polledJob.status === 'failed') { setJobResult(polledJob); setCsvState('failed') }
    else if (polledJob.status === 'running') setStepIndex(p => Math.min(p + 1, 2))
  }, [polledJob])

  const resetCSV = () => {
    setCsvState('idle'); setFile(null); setJobId(null)
    setJobResult(null); setError(null); setStepIndex(0)
  }

  const handleConfirm = async () => {
    if (!file) return
    setCsvState('uploading'); setStepIndex(0)
    try {
      const job = await upload.mutateAsync(file)
      setJobId(job.job_id); setStepIndex(1)
      if (job.status === 'done') { setJobResult(job); setCsvState('done') }
      else if (job.status === 'failed') { setJobResult(job); setCsvState('failed') }
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Upload failed'); setCsvState('failed')
    }
  }

  return (
    <div className="space-y-5">
      {/* Mode toggle */}
      <div className="flex gap-1 bg-[#F3F4F6] p-1 rounded-lg w-fit">
        {['pull', 'csv'].map(m => (
          <button
            key={m}
            onClick={() => { setMode(m); resetCSV() }}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors
              ${mode === m ? 'bg-white shadow-sm text-[#111827]' : 'text-[#6B7280] hover:text-[#374151]'}`}
          >
            {m === 'pull' ? 'Pull from Concur' : 'Upload CSV'}
          </button>
        ))}
      </div>

      {mode === 'pull' ? (
        <TravelPullForm />
      ) : (
        <>
          {csvState === 'idle' && (
            <CSVDropzone
              onFileSelected={f => { setFile(f); setCsvState('preview') }}
              hint="Export from your corporate travel system. Accepts Concur CSV format."
            />
          )}
          {csvState === 'preview' && file && (
            <CSVPreview file={file} onConfirm={handleConfirm} onCancel={resetCSV} />
          )}
          {csvState === 'uploading' && (
            <div className="py-8">
              <StepIndicator steps={STEPS} currentStep={stepIndex} status="running" />
            </div>
          )}
          {csvState === 'done' && jobResult && (
            <div className="space-y-4">
              <StepIndicator steps={STEPS} currentStep={STEPS.length - 1} status="done" />
              <JobResult job={jobResult} />
            </div>
          )}
          {csvState === 'failed' && (
            <div className="space-y-4">
              <div className="bg-[#FEE2E2] border border-[#FCA5A5] rounded-md px-4 py-3">
                <p className="text-sm text-[#991B1B]">{error ?? jobResult?.error_message ?? 'An error occurred.'}</p>
              </div>
              <Button variant="secondary" onClick={resetCSV}>Try Again</Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
