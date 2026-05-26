import React from 'react'

interface InputProps {
  label: string
  error?: string
  type?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function Input({
  label,
  error,
  type = 'text',
  value,
  onChange,
  placeholder,
  disabled,
  className = '',
}: InputProps) {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <label className="text-sm font-medium text-[#374151]">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          rounded-md border px-3 py-2 text-sm text-[#374151] bg-white
          outline-none transition
          ${error
            ? 'border-[#DC2626] focus:border-[#DC2626] focus:ring-1 focus:ring-[#DC2626]'
            : 'border-[#D1D5DB] focus:border-[#16A34A] focus:ring-1 focus:ring-[#16A34A]'}
          ${disabled ? 'opacity-50 cursor-not-allowed bg-[#F9FAFB]' : ''}
        `}
      />
      {error && <p className="text-xs text-[#DC2626]">{error}</p>}
    </div>
  )
}
