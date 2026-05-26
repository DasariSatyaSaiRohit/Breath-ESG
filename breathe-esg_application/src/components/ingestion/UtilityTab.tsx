import React, { useState } from 'react'
import { CSVDropzone } from './CSVDropzone'
import { CSVPreview } from './CSVPreview'
import { StepIndicator } from '../ui/StepIndicator'
import { JobResult } from './JobResult'
import { Button } from '../ui/Button'
import { useUploadUtilityCSV, useJobPolling } from '../../hooks/useIngestion'
import { IngestionJob } from '../../types'

type State = 'idle' | 'preview' | 'uploading' | 'done' | 'failed'

const STEPS = ['Uploading', 'Parsing', 'Normalizing', 'Done']

export function UtilityTab() {
  const [state, setState] = useState<State>('idle')
  const [file, setFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobResult, setJobResult] = useState<IngestionJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [stepIndex, setStepIndex] = useState(0)

  const upload = useUploadUtilityCSV()

  const { data: polledJob } = useJobPolling(jobId, state === 'uploading')

  React.useEffect(() => {
    if (!polledJob) return
    if (polledJob.status === 'done') {
      setJobResult(polledJob)
      setState('done')
    } else if (polledJob.status === 'failed') {
      setJobResult(polledJob)
      setState('failed')
    } else if (polledJob.status === 'running') {
      setStepIndex(prev => Math.min(prev + 1, 2))
    }
  }, [polledJob])

  const handleFileSelected = (f: File) => {
    setFile(f)
    setState('preview')
  }

  const handleConfirm = async () => {
    if (!file) return
    setState('uploading')
    setStepIndex(0)
    try {
      const job = await upload.mutateAsync(file)
      setJobId(job.job_id)
      setStepIndex(1)
      if (job.status === 'done') {
        setJobResult(job)
        setState('done')
      } else if (job.status === 'failed') {
        setJobResult(job)
        setState('failed')
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Upload failed')
      setState('failed')
    }
  }

  const reset = () => {
    setState('idle')
    setFile(null)
    setJobId(null)
    setJobResult(null)
    setError(null)
    setStepIndex(0)
  }

  if (state === 'idle') {
    return (
      <CSVDropzone
        onFileSelected={handleFileSelected}
        hint="Accepts CSV exports from your utility provider. Max 50MB."
      />
    )
  }

  if (state === 'preview' && file) {
    return <CSVPreview file={file} onConfirm={handleConfirm} onCancel={reset} />
  }

  if (state === 'uploading') {
    return (
      <div className="py-8">
        <StepIndicator steps={STEPS} currentStep={stepIndex} status="running" />
        <p className="text-center text-sm text-[#6B7280] mt-6">Processing your file, please wait…</p>
      </div>
    )
  }

  if (state === 'done' && jobResult) {
    return (
      <div className="space-y-4">
        <StepIndicator steps={STEPS} currentStep={STEPS.length - 1} status="done" />
        <JobResult job={jobResult} />
      </div>
    )
  }

  // failed
  return (
    <div className="space-y-4">
      <div className="bg-[#FEE2E2] border border-[#FCA5A5] rounded-md px-4 py-3">
        <p className="text-sm text-[#991B1B]">{error ?? jobResult?.error_message ?? 'An error occurred.'}</p>
      </div>
      <Button variant="secondary" onClick={reset}>Try Again</Button>
    </div>
  )
}
