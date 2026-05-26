import React from 'react'
import { Toast as ToastType } from '../../types'
import { useToast } from '../../hooks/useToast'

interface ToastProps {
  toast: ToastType
  onClose: (id: string) => void
}

export function Toast({ toast, onClose }: ToastProps) {
  const isSuccess = toast.type === 'success'

  return (
    <div
      className={`flex items-start gap-3 bg-white shadow-md rounded-md border-l-4 px-4 py-3 min-w-[280px]
        ${isSuccess ? 'border-l-[#16A34A]' : 'border-l-[#DC2626]'}`}
    >
      <div className="flex-shrink-0 mt-0.5">
        {isSuccess ? (
          <svg className="h-4 w-4 text-[#16A34A]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="h-4 w-4 text-[#DC2626]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
      </div>
      <p className="text-sm text-[#374151] flex-1">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="text-[#9CA3AF] hover:text-[#6B7280] flex-shrink-0"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map(t => (
        <Toast key={t.id} toast={t} onClose={removeToast} />
      ))}
    </div>
  )
}
