import React from 'react'
import { useNavigate } from 'react-router-dom'
import { IngestionJob } from '../../types'
import { Card } from '../ui/Card'

interface JobResultProps {
  job: IngestionJob
}

export function JobResult({ job }: JobResultProps) {
  const navigate = useNavigate()
  const flagged = job.records_total - job.records_success - job.records_failed

  return (
    <Card className="p-6 space-y-4">
      <h3 className="text-sm font-semibold text-[#111827]">Ingestion Complete</h3>

      <div className="flex gap-6">
        <div className="text-center">
          <p className="text-2xl font-semibold text-[#16A34A]">{job.records_success}</p>
          <p className="text-xs text-[#6B7280] mt-0.5">Imported</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-semibold text-[#DC2626]">{job.records_failed}</p>
          <p className="text-xs text-[#6B7280] mt-0.5">Failed</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-semibold text-[#D97706]">{flagged}</p>
          <p className="text-xs text-[#6B7280] mt-0.5">Flagged</p>
        </div>
      </div>

      {job.status === 'failed' && job.error_message && (
        <div className="bg-[#FEE2E2] border border-[#FCA5A5] rounded-md px-4 py-3">
          <p className="text-sm text-[#991B1B]">{job.error_message}</p>
        </div>
      )}

      <button
        onClick={() => navigate('/review')}
        className="text-sm text-[#16A34A] hover:underline font-medium"
      >
        View in Review Dashboard →
      </button>
    </Card>
  )
}
