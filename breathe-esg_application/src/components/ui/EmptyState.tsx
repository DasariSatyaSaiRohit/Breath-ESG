import React from 'react'

interface EmptyStateProps {
  icon: React.ReactNode
  heading: string
  subtext: string
}

export function EmptyState({ icon, heading, subtext }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="h-10 w-10 text-[#9CA3AF]">{icon}</div>
      <p className="text-[15px] font-medium text-[#374151]">{heading}</p>
      <p className="text-[13px] text-[#6B7280]">{subtext}</p>
    </div>
  )
}
