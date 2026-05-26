import React, { useState, useEffect } from 'react'
import { Drawer } from '../ui/Drawer'
import { Button } from '../ui/Button'
import { EsgRecord, PatchRecordPayload } from '../../types'
import { usePatchRecord } from '../../hooks/useRecords'
import { useToast } from '../../hooks/useToast'

interface EditDrawerProps {
  record: EsgRecord | null
  onClose: () => void
  onSaved: () => void
}

export function EditDrawer({ record, onClose, onSaved }: EditDrawerProps) {
  const patch = usePatchRecord()
  const { addToast } = useToast()

  const [normalizedValue, setNormalizedValue] = useState('')
  const [normalizedUnit,  setNormalizedUnit]  = useState('')
  const [description,     setDescription]     = useState('')
  const [flagReason,      setFlagReason]      = useState('')

  useEffect(() => {
    if (record) {
      setNormalizedValue(record.normalized_value ?? '')
      setNormalizedUnit(record.normalized_unit)
      setDescription(record.description)
      setFlagReason(record.flag_reason ?? '')
    }
  }, [record])

  const handleSave = async () => {
    if (!record) return

    // Build payload with only changed fields
    // raw_data is intentionally excluded — it is read-only
    const payload: PatchRecordPayload = {}
    if (normalizedValue !== (record.normalized_value ?? ''))
      payload.normalized_value = normalizedValue
    if (normalizedUnit !== record.normalized_unit)
      payload.normalized_unit = normalizedUnit
    if (description !== record.description)
      payload.description = description
    if (flagReason !== (record.flag_reason ?? ''))
      payload.flag_reason = flagReason

    try {
      // record.id is the prefixed string e.g. "utility_42"
      await patch.mutateAsync({ id: record.id, payload })
      addToast('success', 'Record updated')
      onSaved()
      onClose()
    } catch {
      addToast('error', 'Failed to update record')
    }
  }

  const labelClass = 'text-xs font-medium text-[#6B7280] mb-1 block'
  const inputClass =
    'w-full rounded-md border border-[#D1D5DB] px-3 py-2 text-sm text-[#374151] ' +
    'focus:outline-none focus:border-[#16A34A] focus:ring-1 focus:ring-[#16A34A]'

  return (
    <Drawer open={record !== null} onClose={onClose} title="Edit Record">
      {record && (
        <div className="space-y-5">
          {/* Section 1 — Original source data (read-only, dynamic) */}
          <div>
            <p className="text-xs font-semibold text-[#111827] uppercase tracking-wider mb-2">
              Original Source Data
            </p>
            <div className="rounded-md border border-[#E5E7EB] divide-y divide-[#E5E7EB]">
              {Object.entries(record.raw_data ?? {}).map(([key, value]) => (
                <div
                  key={key}
                  className="flex justify-between px-3 py-2 text-sm"
                >
                  <span className="text-[#6B7280] flex-shrink-0 mr-3">{key}</span>
                  <span
                    className="font-mono text-[#374151] truncate max-w-[60%] text-right"
                    title={value}
                  >
                    {value || '—'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <hr className="border-[#E5E7EB]" />

          {/* Section 2 — Normalized values (editable, always fixed) */}
          <div>
            <p className="text-xs font-semibold text-[#111827] uppercase tracking-wider mb-3">
              Normalized Values
            </p>

            <div className="space-y-3">
              <div>
                <label className={labelClass}>Normalized Value</label>
                <input
                  type="number"
                  value={normalizedValue}
                  onChange={e => setNormalizedValue(e.target.value)}
                  className={inputClass}
                />
              </div>

              <div>
                <label className={labelClass}>Normalized Unit</label>
                <input
                  type="text"
                  value={normalizedUnit}
                  onChange={e => setNormalizedUnit(e.target.value)}
                  className={inputClass}
                />
              </div>

              <div>
                <label className={labelClass}>Description</label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  rows={3}
                  className={`${inputClass} resize-none`}
                />
              </div>

              <div>
                <label className={labelClass}>Flag Reason (optional)</label>
                <textarea
                  value={flagReason}
                  onChange={e => setFlagReason(e.target.value)}
                  rows={2}
                  className={`${inputClass} resize-none`}
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              variant="primary"
              onClick={handleSave}
              loading={patch.isPending}
            >
              Save Changes
            </Button>
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </Drawer>
  )
}
