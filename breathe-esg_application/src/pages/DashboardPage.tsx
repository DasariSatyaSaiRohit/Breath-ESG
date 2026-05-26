import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useRecordsQuery } from '../hooks/useRecords'
import { Card } from '../components/ui/Card'
import { CardSkeleton } from '../components/ui/Skeleton'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { JobStatus, SourceTypeLabel } from '../types'

// TODO: Replace with actual GET /api/ingestion/jobs/ endpoint once available

const sourceTypeLabels: Record<SourceTypeLabel, string> = {
  utility_csv: 'Utility CSV',
  travel_api: 'Travel — Concur API',
  travel_csv: 'Travel CSV',
}

interface MetricCardProps {
  label: string
  value: number | undefined
  loading: boolean
  color?: string
}

function MetricCard({ label, value, loading, color = '#16A34A' }: MetricCardProps) {
  return (
    <Card className="p-5">
      {loading ? (
        <CardSkeleton />
      ) : (
        <>
          <p className="text-3xl font-semibold" style={{ color }}>{value ?? 0}</p>
          <p className="text-sm text-[#6B7280] mt-1">{label}</p>
        </>
      )}
    </Card>
  )
}

export function DashboardPage() {
  const navigate = useNavigate()

  const total = useRecordsQuery({})
  const pending = useRecordsQuery({ status: 'pending' })
  const approved = useRecordsQuery({ status: 'approved' })
  const failed = useRecordsQuery({ status: 'failed' })
  const flagged = useRecordsQuery({ status: 'flagged' })

  const failedFlagged = (failed.data?.count ?? 0) + (flagged.data?.count ?? 0)

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#111827]">Dashboard</h1>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard label="Total Records" value={total.data?.count} loading={total.isLoading} />
        <MetricCard label="Pending Review" value={pending.data?.count} loading={pending.isLoading} color="#D97706" />
        <MetricCard label="Approved" value={approved.data?.count} loading={approved.isLoading} />
        <MetricCard label="Failed / Flagged" value={failedFlagged} loading={failed.isLoading || flagged.isLoading} color="#DC2626" />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-[#111827] mb-3">Quick Actions</h2>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=utility')}>
            Upload Utility CSV
          </Button>
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=travel&mode=pull')}>
            Pull Travel Data
          </Button>
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=travel&mode=csv')}>
            Upload Travel CSV
          </Button>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-sm font-semibold text-[#111827] mb-3">Recent Records</h2>
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#F9FAFB]">
                  {['Source', 'Date', 'Normalized', 'Scope', 'Status'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {total.isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-[#E5E7EB]">
                      {[...Array(5)].map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 bg-[#E5E7EB] rounded animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (total.data?.results ?? []).slice(0, 5).map(r => (
                  <tr key={r.id} className="border-b border-[#E5E7EB] hover:bg-[#F9FAFB]">
                    <td className="px-4 py-3 text-sm text-[#374151]">{r.source_type}</td>
                    <td className="px-4 py-3 text-sm text-[#374151]">{r.activity_date}</td>
                    <td className="px-4 py-3 text-sm text-[#374151]">{r.normalized_value} {r.normalized_unit}</td>
                    <td className="px-4 py-3 text-sm text-[#374151]">{r.scope.replace('_', ' ')}</td>
                    <td className="px-4 py-3"><Badge variant={r.status}>{r.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
