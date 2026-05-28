import React, { useState } from 'react'
import { SourceType, RecordFilters, EsgRecord } from '../../types'
import {
  useRecordsQuery,
  useApproveRecord,
  useBulkApprove,
  useLockRecords,
} from '../../hooks/useRecords'
import { buildTableColumns } from '../../utils/tableColumns'
import { RecordRow } from './RecordRow'
import { EditDrawer } from './EditDrawer'
import { FlagPopover } from './FlagPopover'
import { TableSkeleton } from '../ui/Skeleton'
import { EmptyState } from '../ui/EmptyState'
import { Pagination } from '../ui/Pagination'
import { Button } from '../ui/Button'
import { useToast } from '../../hooks/useToast'
import { useAuth } from '../../context/AuthContext'

interface RecordTableProps {
  activeSource: SourceType
  filters: RecordFilters
  onFiltersChange: (f: RecordFilters) => void
}

const PAGE_SIZE = 25

export function RecordTable({ activeSource, filters, onFiltersChange }: RecordTableProps) {
  const queryFilters: RecordFilters = { ...filters, source: activeSource }

  const { data, isLoading, isFetching } = useRecordsQuery(queryFilters)
  const approve      = useApproveRecord()
  const bulk         = useBulkApprove()
  const lock         = useLockRecords()
  const { addToast } = useToast()
  const { auth }     = useAuth()

  const [selectedIds,   setSelectedIds]   = useState<Set<string>>(new Set())
  const [editRecord,    setEditRecord]     = useState<EsgRecord | null>(null)
  const [flagRecordId,  setFlagRecordId]   = useState<string | null>(null)

  const records = data?.results ?? []

  // Use stale column count while refetching so shimmer width matches
  const tableColumns     = buildTableColumns(data?.columns ?? [])
  const shimmerColCount  = tableColumns.length || 6

  // Checkbox helpers
  const allSelected = records.length > 0 && records.every(r => selectedIds.has(r.id))

  const toggleAll = () =>
    setSelectedIds(allSelected ? new Set() : new Set(records.map(r => r.id)))

  const toggleOne = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const handleApprove = async (id: string) => {
    try {
      await approve.mutateAsync(id)
      addToast('success', 'Record approved')
    } catch {
      addToast('error', 'Failed to approve record')
    }
  }

  const handleBulkApprove = async () => {
    try {
      const result = await bulk.mutateAsync([...selectedIds])
      addToast('success', `${result.approved_count} records approved`)
      setSelectedIds(new Set())
    } catch {
      addToast('error', 'Bulk approval failed')
    }
  }

  const handleLock = async () => {
    try {
      const result = await lock.mutateAsync([...selectedIds])
      addToast('success', `${result.locked_count} records locked`)
      setSelectedIds(new Set())
    } catch {
      addToast('error', 'Lock failed')
    }
  }

  const selectedRecords = records.filter(r => selectedIds.has(r.id))
  const lockDisabled    = selectedRecords.some(r => r.status !== 'approved')
  const isAdmin         = auth.user?.role === 'admin'
  const colSpan         = shimmerColCount + 2 // checkbox + actions

  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg shadow-sm">
      {/* Thin progress bar on subsequent fetches (tab switch / page change) */}
      {isFetching && !isLoading && (
        <div className="h-0.5 bg-[#16A34A] animate-pulse w-full rounded-t-lg" />
      )}

      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="px-4 py-2.5 border-b border-[#E5E7EB] flex items-center gap-3 flex-wrap">
          <Button variant="primary" onClick={handleBulkApprove} loading={bulk.isPending}>
            Approve Selected ({selectedIds.size})
          </Button>
          {isAdmin && (
            <Button
              variant="secondary"
              onClick={handleLock}
              loading={lock.isPending}
              disabled={lockDisabled}
            >
              Lock Selected ({selectedIds.size})
            </Button>
          )}
          <button
            onClick={() => setSelectedIds(new Set())}
            className="text-sm text-[#6B7280] hover:text-[#374151]"
          >
            Clear selection
          </button>
          {isAdmin && lockDisabled && (
            <span className="text-xs text-[#9CA3AF]">
              All selected records must be approved before locking
            </span>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          {/* ── SHIMMER thead ── shown during initial load */}
          {isLoading ? (
            <>
              <thead>
                <tr className="bg-[#F9FAFB]">
                  {/* Checkbox */}
                  <th className="px-4 py-3 border-b border-[#E5E7EB] w-10">
                    <div className="h-3 w-4 bg-[#E5E7EB] rounded animate-pulse" />
                  </th>
                  {Array.from({ length: shimmerColCount }).map((_, i) => (
                    <th key={i} className="px-4 py-3 border-b border-[#E5E7EB]">
                      <div className="h-3 w-20 bg-[#E5E7EB] rounded animate-pulse" />
                    </th>
                  ))}
                  {/* Actions */}
                  <th className="px-4 py-3 border-b border-[#E5E7EB]">
                    <div className="h-3 w-16 bg-[#E5E7EB] rounded animate-pulse" />
                  </th>
                </tr>
              </thead>
              {/* SHIMMER tbody — 8 rows */}
              <tbody>
                {Array.from({ length: 8 }).map((_, ri) => (
                  <tr key={ri} className="border-b border-[#E5E7EB]">
                    <td className="px-4 py-3">
                      <div className="h-4 w-4 bg-[#E5E7EB] rounded animate-pulse" />
                    </td>
                    {Array.from({ length: shimmerColCount }).map((_, ci) => (
                      <td key={ci} className="px-4 py-3">
                        <div className="h-4 w-full bg-[#E5E7EB] rounded animate-pulse" />
                      </td>
                    ))}
                    <td className="px-4 py-3">
                      <div className="h-4 w-16 bg-[#E5E7EB] rounded animate-pulse" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </>
          ) : (
            <>
              <thead>
                <tr className="bg-[#F9FAFB]">
                  <th className="px-4 py-3 border-b border-[#E5E7EB] w-10">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={toggleAll}
                      className="rounded border-[#D1D5DB] text-[#16A34A] focus:ring-[#16A34A]"
                    />
                  </th>
                  {tableColumns.map(col => (
                    <th
                      key={col.key}
                      className="px-4 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB] whitespace-nowrap"
                    >
                      {col.header}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]">
                    Actions
                  </th>
                </tr>
              </thead>

              {records.length === 0 ? (
                <tbody>
                  <tr>
                    <td colSpan={colSpan}>
                      <EmptyState
                        icon={
                          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="h-10 w-10">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                        }
                        heading="No records found"
                        subtext="Try adjusting your filters or switching tabs."
                      />
                    </td>
                  </tr>
                </tbody>
              ) : (
                <tbody>
                  {records.map(record => (
                    <React.Fragment key={record.id}>
                      <RecordRow
                        record={record}
                        columns={tableColumns}
                        selected={selectedIds.has(record.id)}
                        onSelect={toggleOne}
                        onApprove={handleApprove}
                        onFlag={id => setFlagRecordId(flagRecordId === id ? null : id)}
                        onEdit={setEditRecord}
                      />
                      {flagRecordId === record.id && (
                        <tr>
                          <td colSpan={colSpan} className="relative p-0">
                            <div className="absolute left-4 z-30 mt-1">
                              <FlagPopover
                                recordId={record.id}
                                onClose={() => setFlagRecordId(null)}
                                onFlagged={() => setFlagRecordId(null)}
                              />
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              )}
            </>
          )}
        </table>
      </div>

      {/* Pagination */}
      {data && data.count > 0 && (
        <Pagination
          page={filters.page ?? 1}
          totalCount={data.count}
          pageSize={PAGE_SIZE}
          onPageChange={page => onFiltersChange({ ...filters, page })}
        />
      )}

      {/* Edit drawer */}
      <EditDrawer
        record={editRecord}
        onClose={() => setEditRecord(null)}
        onSaved={() => setEditRecord(null)}
      />
    </div>
  )
}
