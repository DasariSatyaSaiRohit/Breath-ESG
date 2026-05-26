import React, { useEffect, useState } from 'react'
import { Button } from '../ui/Button'

interface CSVPreviewProps {
  file: File
  onConfirm: () => void
  onCancel: () => void
}

export function CSVPreview({ file, onConfirm, onCancel }: CSVPreviewProps) {
  const [headers, setHeaders] = useState<string[]>([])
  const [rows, setRows] = useState<string[][]>([])

  useEffect(() => {
    const reader = new FileReader()
    reader.onload = e => {
      const text = e.target?.result as string
      const lines = text.split('\n').filter(l => l.trim())
      const parsed = lines.slice(0, 6).map(line =>
        line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''))
      )
      setHeaders(parsed[0] ?? [])
      setRows(parsed.slice(1))
    }
    reader.readAsText(file)
  }, [file])

  const fileSize = (file.size / 1024).toFixed(1)

  return (
    <div className="space-y-4">
      <p className="text-[13px] text-[#6B7280]">
        {file.name} — {fileSize} KB
      </p>
      <div className="overflow-x-auto border border-[#E5E7EB] rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-[#F9FAFB]">
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider border-b border-[#E5E7EB]">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} className="border-b border-[#E5E7EB] last:border-0">
                {row.map((cell, ci) => (
                  <td key={ci} className="px-3 py-2 text-[#374151]">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-3">
        <Button variant="primary" onClick={onConfirm}>Confirm Upload</Button>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  )
}
