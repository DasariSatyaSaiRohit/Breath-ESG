import React, { useState } from 'react'

interface JsonViewerProps {
  data: Record<string, unknown> | null
}

export function JsonViewer({ data }: JsonViewerProps) {
  const [expanded, setExpanded] = useState(false)

  if (!data) return <span className="text-[#9CA3AF]">—</span>

  return (
    <div className="text-xs">
      {expanded ? (
        <>
          <pre className="bg-[#F9FAFB] border border-[#E5E7EB] rounded p-2 font-mono text-[12px] text-[#374151] whitespace-pre-wrap max-w-xs overflow-auto max-h-40">
            {JSON.stringify(data, null, 2)}
          </pre>
          <button
            onClick={() => setExpanded(false)}
            className="text-[#16A34A] hover:underline mt-1"
          >
            Hide
          </button>
        </>
      ) : (
        <button
          onClick={() => setExpanded(true)}
          className="text-[#16A34A] hover:underline"
        >
          View
        </button>
      )}
    </div>
  )
}
