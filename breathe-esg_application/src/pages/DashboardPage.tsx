import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboardSummary } from '../hooks/useDashboard'
import { Card } from '../components/ui/Card'
import { CardSkeleton } from '../components/ui/Skeleton'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'
import { formatTimestamp } from '../utils/dateFormat'

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

const sourceLabels: Record<string, string> = {
  utility_csv:      'Utility CSV',
  travel_api:       'Travel — Concur API',
  travel_csv:       'Travel CSV',
  sap_csv:          'SAP Procurement',
  sap_procurement:  'SAP Procurement',
  utility:          'Utility',
  travel:           'Travel',
  sap:              'SAP',
}

const scopeColors: Record<string, string> = {
  scope_1: '#16A34A',
  scope_2: '#2563EB',
  scope_3: '#9333EA',
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { tenantConfig } = useAuth()
  const tz = tenantConfig?.timezone ?? 'UTC'

  // Single API call — E6c
  const { data, isLoading } = useDashboardSummary()

  const stats            = data?.stats
  const scopeBreakdown   = data?.scope_breakdown
  const sourceBreakdown  = data?.source_breakdown
  const recentIngestions = data?.recent_ingestions ?? []
  const monthlyTrend     = data?.monthly_trend ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#111827]">Dashboard</h1>

      {/* Stat cards — single loading state */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard label="Total Records"   value={stats?.total_records}  loading={isLoading} />
        <MetricCard label="Pending Review"  value={stats?.pending_review} loading={isLoading} color="#D97706" />
        <MetricCard label="Approved"        value={stats?.approved}       loading={isLoading} />
        <MetricCard label="Failed / Flagged"
          value={(stats?.failed ?? 0) + (stats?.flagged ?? 0)}
          loading={isLoading}
          color="#DC2626"
        />
      </div>

      {/* Scope + Source breakdown */}
      <div className="grid grid-cols-2 gap-4">

        {/* Source breakdown */}
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-[#111827] mb-4">Source Breakdown</h2>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => <CardSkeleton key={i} />)}
            </div>
          ) : (
            <div className="space-y-3">
              {(['utility', 'travel', 'sap'] as const).map(src => {
                const val   = sourceBreakdown?.[src] ?? 0
                const total = (sourceBreakdown?.utility ?? 0) + (sourceBreakdown?.travel ?? 0) + (sourceBreakdown?.sap ?? 0)
                const pct   = total > 0 ? Math.round((val / total) * 100) : 0
                return (
                  <div key={src}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[#374151] font-medium capitalize">{src}</span>
                      <span className="text-[#6B7280]">{val} ({pct}%)</span>
                    </div>
                    <div className="h-2 bg-[#F3F4F6] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#16A34A] transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </div>

      {/* Monthly trend */}
      {monthlyTrend.length > 0 && (
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-[#111827] mb-4">Monthly Trend</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#F9FAFB]">
                  {['Month', 'Scope 1', 'Scope 2', 'Scope 3'].map(h => (
                    <th key={h} className="px-4 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {monthlyTrend.map(row => (
                  <tr key={row.month} className="border-b border-[#E5E7EB] hover:bg-[#F9FAFB]">
                    <td className="px-4 py-2 text-[#374151]">{row.month}</td>
                    <td className="px-4 py-2 text-[#374151]">{row.scope_1}</td>
                    <td className="px-4 py-2 text-[#374151]">{row.scope_2}</td>
                    <td className="px-4 py-2 text-[#374151]">{row.scope_3}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-[#111827] mb-3">Quick Actions</h2>
        <div className="flex gap-3 flex-wrap">
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=utility')}>
            Upload Utility CSV
          </Button>
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=travel&mode=pull')}>
            Pull Travel Data
          </Button>
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=travel&mode=csv')}>
            Upload Travel CSV
          </Button>
          <Button variant="secondary" onClick={() => navigate('/ingest?tab=sap')}>
            Upload SAP CSV
          </Button>
        </div>
      </div>

      {/* Recent Ingestions */}
      <div>
        <h2 className="text-sm font-semibold text-[#111827] mb-3">Recent Ingestions</h2>
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#F9FAFB]">
                  {['Source', 'Started', 'Rows', 'Status'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-[#E5E7EB]">
                      {[...Array(4)].map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 bg-[#E5E7EB] rounded animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : recentIngestions.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-sm text-[#6B7280]">
                      No ingestion jobs yet.
                    </td>
                  </tr>
                ) : (
                  recentIngestions.map(job => (
                    <tr key={job.job_id} className="border-b border-[#E5E7EB] hover:bg-[#F9FAFB]">
                      <td className="px-4 py-3 text-sm text-[#374151]">
                        {sourceLabels[job.source] ?? job.source}
                      </td>
                      <td className="px-4 py-3 text-sm text-[#374151]">
                        {formatTimestamp(job.created_at, tz)}
                      </td>
                      <td className="px-4 py-3 text-sm text-[#374151]">{job.row_count}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          job.status === 'completed' ? 'bg-[#DCFCE7] text-[#166534]' :
                          job.status === 'processing' ? 'bg-[#FEF9C3] text-[#854D0E]' :
                          job.status === 'partial'    ? 'bg-[#FFEDD5] text-[#9A3412]' :
                          'bg-[#FEE2E2] text-[#991B1B]'
                        }`}>
                          {job.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
