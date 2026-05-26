import React from 'react'

interface SkeletonProps {
  rows?: number
  columns?: number
}

const shimmer = `
  relative overflow-hidden bg-[#E5E7EB] rounded
  before:absolute before:inset-0
  before:bg-gradient-to-r before:from-transparent before:via-white/60 before:to-transparent
  before:animate-[shimmer_1.5s_infinite]
`

export function TableSkeleton({ rows = 5, columns = 6 }: SkeletonProps) {
  return (
    <tbody>
      {Array.from({ length: rows }).map((_, ri) => (
        <tr key={ri} className="border-b border-[#E5E7EB]">
          {Array.from({ length: columns }).map((_, ci) => (
            <td key={ci} className="px-4 py-3">
              <div className={`h-4 w-full ${shimmer}`} />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  )
}

export function CardSkeleton() {
  return <div className={`h-24 w-full rounded-lg ${shimmer}`} />
}
