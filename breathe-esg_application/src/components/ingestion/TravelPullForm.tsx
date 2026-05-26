import React, { useState } from 'react'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { StepIndicator } from '../ui/StepIndicator'
import { JobResult } from './JobResult'
import { usePullTravel, useJobPolling } from '../../hooks/useIngestion'
import { IngestionJob } from '../../types'

type State = 'idle' | 'pulling' | 'done' | 'failed'

const STEPS = ['Connecting to Concur', 'Fetching itineraries', 'Normalizing', 'Done']

export function TravelPullForm() {
  const [state, setState] = useState<State>('idle')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [tripId, setTripId] = useState('')
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobResult, setJobResult] = useState<IngestionJob | null>(null)
  const [stepIndex, setStepIndex] = useState(0)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const pull = usePullTravel()

  const { data: polledJob } = useJobPolling(jobId, state === 'pulling')

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

  const validate = () => {
    const e: Record<string, string> = {}
    if (!dateFrom) e.dateFrom = 'Start date is required'
    if (!dateTo) e.dateTo = 'End date is required'
    return e
  }

  const handleSubmit = async () => {
    const e = validate()
    if (Object.keys(e).length > 0) { setErrors(e); return }
    setErrors({})
    setState('pulling')
    setStepIndex(0)
    try {
      const params: { date_from: string; date_to: string; trip_id?: string } = {
        date_from: dateFrom,
        date_to: dateTo,
      }
      if (tripId) params.trip_id = tripId
      const job = await pull.mutateAsync(params)
      setJobId(job.job_id)
      setStepIndex(1)
      if (job.status === 'done') { setJobResult(job); setState('done') }
      else if (job.status === 'failed') { setJobResult(job); setState('failed') }
    } catch (err: any) {
      setJobResult({ job_id: '', status: 'failed', records_total: 0, records_success: 0, records_failed: 0, error_message: err?.response?.data?.detail ?? 'Pull failed' })
      setState('failed')
    }
  }

  const reset = () => {
    setState('idle')
    setJobId(null)
    setJobResult(null)
    setStepIndex(0)
  }

  if (state === 'idle') {
    return (
      <div className="space-y-4 max-w-sm">
        <Input label="Date From" type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} error={errors.dateFrom} />
        <Input label="Date To" type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} error={errors.dateTo} />
        <Input label="Trip ID (optional)" value={tripId} onChange={e => setTripId(e.target.value)} placeholder="e.g. TRP-12345" />
        <Button variant="primary" onClick={handleSubmit} loading={pull.isPending}>Pull Data</Button>
      </div>
    )
  }

  if (state === 'pulling') {
    return (
      <div className="py-8">
        <StepIndicator steps={STEPS} currentStep={stepIndex} status="running" />
        <p className="text-center text-sm text-[#6B7280] mt-6">Connecting to Concur and fetching travel data…</p>
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

  return (
    <div className="space-y-4">
      <div className="bg-[#FEE2E2] border border-[#FCA5A5] rounded-md px-4 py-3">
        <p className="text-sm text-[#991B1B]">{jobResult?.error_message ?? 'An error occurred.'}</p>
      </div>
      <Button variant="secondary" onClick={reset}>Try Again</Button>
    </div>
  )
}
