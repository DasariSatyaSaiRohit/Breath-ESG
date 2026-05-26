import React, { useState } from 'react'
import { AuditFilters } from '../../types'
import { useAuditQuery } from '../../hooks/useAudit'
import { Badge } from '../ui/Badge'
import { JsonViewer } from './JsonViewer'
import { TableSkeleton } from '../ui/Skeleton'
import { EmptyState } from '../ui/EmptyState'
import { Pagination } from '../ui/Pagination'

interface AuditTableProps {
  filters: AuditFilters
  onFiltersChange?: (f: AuditFilters) => void
}

const PAGE_SIZE = 25

function formatTimestamp(ts: string): string {
  const d = new Date(ts)
  return (
    d.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }) +
    ', ' +
    d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  )
}

export function AuditTable({ filters, onFiltersChange }: AuditTableProps) {
  const { data, isLoading } = useAuditQuery(filters)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const logs = data?.results ?? []

  const copyId = (id: string) => {
    navigator.clipboard.writeText(id).then(() => {
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 1500)
    })
  }

  const columns = [
    'Timestamp',
    'User',
    'Action',
    'Source Type',
    'Record ID',
    'Old Value',
    'New Value',
  ]

  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-[#F9FAFB]">
              {columns.map(col => (
                <th
                  key={col}
                  className="px-4 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>

          {isLoading ? (
            <TableSkeleton rows={5} columns={columns.length} />
          ) : logs.length === 0 ? (
            <tbody>
              <tr>
                <td colSpan={columns.length}>
                  <EmptyState
                    icon={
                      <svg
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        className="h-10 w-10"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                        />
                      </svg>
                    }
                    heading="No audit logs found"
                    subtext="Adjust the date range or action filter to find entries."
                  />
                </td>
              </tr>
            </tbody>
          ) : (
            <tbody>
              {logs.map(log => {
                const idStr = String(log.id)

                return (
                  <tr
                    key={log.id}
                    className="border-b border-[#E5E7EB] hover:bg-[#F9FAFB]"
                  >
                    {/* Timestamp */}
                    <td className="px-4 py-3 text-sm text-[#374151] whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </td>

                    {/* User */}
                    <td className="px-4 py-3 text-sm text-[#374151]">
                      {log.user}
                    </td>

                    {/* Action — 'locked' variant now supported */}
                    <td className="px-4 py-3">
                      <Badge variant={log.action}>{log.action}</Badge>
                    </td>

                    {/* record_source_type — render 'utility' | 'travel' | '—' */}
                    <td className="px-4 py-3 text-sm text-[#374151]">
                      {log.record_source_type ?? '—'}
                    </td>

                    {/* record_id — plain integer as-is, or '—' */}
                    <td className="px-4 py-3">
                      {log.record_id !== null ? (
                        <div className="relative inline-block">
                          <button
                            onClick={() => copyId(idStr)}
                            className="font-mono text-xs text-[#6B7280] hover:text-[#374151] transition-colors"
                            title={String(log.record_id)}
                          >
                            {log.record_id}
                          </button>
                          {copiedId === idStr && (
                            <span className="absolute -top-6 left-0 bg-[#111827] text-white text-xs px-2 py-0.5 rounded whitespace-nowrap">
                              Copied!
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-[#9CA3AF]">—</span>
                      )}
                    </td>

                    {/* Old Value */}
                    <td className="px-4 py-3">
                      <JsonViewer data={log.old_value} />
                    </td>

                    {/* New Value */}
                    <td className="px-4 py-3">
                      <JsonViewer data={log.new_value} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          )}
        </table>
      </div>

      {data && data.count > 0 && (
        <Pagination
          page={filters.page ?? 1}
          totalCount={data.count}
          pageSize={PAGE_SIZE}
          onPageChange={page => onFiltersChange?.({ ...filters, page })}
        />
      )}
    </div>
  )
}
