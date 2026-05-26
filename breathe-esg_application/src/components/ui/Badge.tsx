import React from 'react'
import { RecordStatus, AuditAction } from '../../types'

type BadgeVariant = RecordStatus | AuditAction

interface BadgeProps {
  variant: BadgeVariant
  children: React.ReactNode
}

const styles: Record<BadgeVariant, string> = {
  // Record status
  pending:       'bg-[#FEF9C3] text-[#854D0E]',
  approved:      'bg-[#DCFCE7] text-[#166534]',
  flagged:       'bg-[#FFEDD5] text-[#9A3412]',
  failed:        'bg-[#FEE2E2] text-[#991B1B]',
  // Audit actions
  created:       'bg-[#DBEAFE] text-[#1E40AF]',
  edited:        'bg-[#FEF3C7] text-[#92400E]',
  bulk_approved: 'bg-[#CCFBF1] text-[#115E59]',
  locked:        'bg-[#F3E8FF] text-[#6B21A8]',
}

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[variant]}`}
    >
      {children}
    </span>
  )
}
