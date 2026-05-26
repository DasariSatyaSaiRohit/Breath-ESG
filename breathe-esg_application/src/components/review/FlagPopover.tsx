import React, { useState } from 'react'
import { useFlagRecord } from '../../hooks/useRecords'
import { useToast } from '../../hooks/useToast'
import { Button } from '../ui/Button'

interface FlagPopoverProps {
  recordId: string
  onClose: () => void
  onFlagged: () => void
}

export function FlagPopover({ recordId, onClose, onFlagged }: FlagPopoverProps) {
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const flag = useFlagRecord()
  const { addToast } = useToast()

  const handleSubmit = async () => {
    if (!reason.trim()) { setError('Reason is required'); return }
    try {
      await flag.mutateAsync({ id: recordId, reason: reason.trim() })
      addToast('success', 'Record flagged')
      onFlagged()
      onClose()
    } catch {
      addToast('error', 'Failed to flag record')
    }
  }

  return (
    <div className="absolute z-30 w-[280px] bg-white border border-[#E5E7EB] shadow-lg rounded-lg p-4 space-y-3">
      <p className="text-sm font-medium text-[#111827]">Flag Record</p>
      <div className="space-y-1">
        <textarea
          value={reason}
          onChange={e => { setReason(e.target.value); setError('') }}
          placeholder="Reason for flagging…"
          rows={3}
          className="w-full rounded-md border border-[#D1D5DB] px-3 py-2 text-sm text-[#374151]
            focus:outline-none focus:border-[#16A34A] focus:ring-1 focus:ring-[#16A34A] resize-none"
        />
        {error && <p className="text-xs text-[#DC2626]">{error}</p>}
      </div>
      <div className="flex gap-2">
        <Button variant="danger" onClick={handleSubmit} loading={flag.isPending}>Submit</Button>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
      </div>
    </div>
  )
}
