import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white border border-[#E5E7EB] rounded-lg shadow-sm ${className}`}>
      {children}
    </div>
  )
}
