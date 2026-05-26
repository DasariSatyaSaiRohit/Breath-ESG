import React, { useRef, useState } from 'react'

interface CSVDropzoneProps {
  onFileSelected: (file: File) => void
  hint: string
  accept?: string
}

export function CSVDropzone({ onFileSelected, hint, accept = '.csv' }: CSVDropzoneProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileSelected(file)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFileSelected(file)
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors
        ${dragging
          ? 'border-[#16A34A] bg-[#F0FDF4]'
          : 'border-[#D1D5DB] bg-white hover:border-[#16A34A] hover:bg-[#F0FDF4]'}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={handleChange}
      />
      <svg
        className="h-10 w-10 mx-auto mb-3 text-[#9CA3AF]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
      <p className="text-sm font-medium text-[#374151]">Drop CSV here or click to browse</p>
      <p className="mt-1.5 text-[13px] text-[#6B7280]">{hint}</p>
    </div>
  )
}
