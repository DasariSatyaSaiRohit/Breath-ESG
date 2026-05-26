import React from 'react'
import { TableSkeleton } from './Skeleton'

export interface Column<T> {
  key: string
  header: string
  render?: (row: T) => React.ReactNode
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  loading: boolean
  empty: React.ReactNode
  onRowClick?: (row: T) => void
}

export function Table<T extends { id?: string }>({
  columns,
  data,
  loading,
  empty,
  onRowClick,
}: TableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-[#F9FAFB]">
            {columns.map(col => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        {loading ? (
          <TableSkeleton rows={5} columns={columns.length} />
        ) : data.length === 0 ? (
          <tbody>
            <tr>
              <td colSpan={columns.length}>{empty}</td>
            </tr>
          </tbody>
        ) : (
          <tbody>
            {data.map((row, i) => (
              <tr
                key={(row as any).id ?? i}
                onClick={() => onRowClick?.(row)}
                className={`border-b border-[#E5E7EB] hover:bg-[#F9FAFB] transition-colors ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map(col => (
                  <td key={col.key} className="px-4 py-3 text-sm text-[#374151]">
                    {col.render ? col.render(row) : String((row as any)[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        )}
      </table>
    </div>
  )
}
