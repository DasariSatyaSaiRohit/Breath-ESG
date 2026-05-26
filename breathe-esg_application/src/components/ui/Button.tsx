import React from 'react'

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger'
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
  children: React.ReactNode
  type?: 'button' | 'submit' | 'reset'
  className?: string
}

const variantStyles = {
  primary:   'bg-[#16A34A] text-white hover:bg-[#15803D]',
  secondary: 'bg-white border border-[#D1D5DB] text-[#374151] hover:bg-[#F9FAFB]',
  danger:    'bg-[#DC2626] text-white hover:bg-[#B91C1C]',
}

const Spinner = () => (
  <svg
    className="animate-spin h-4 w-4 mr-2"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
  </svg>
)

export function Button({
  variant = 'primary',
  loading,
  disabled,
  onClick,
  children,
  type = 'button',
  className = '',
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium
        transition-colors
        ${variantStyles[variant]}
        ${isDisabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}
        ${className}
      `}
    >
      {loading && <Spinner />}
      {children}
    </button>
  )
}
