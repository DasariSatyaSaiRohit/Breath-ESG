import React from 'react'
import { useAuth } from '../../context/AuthContext'

export function TopBar() {
  const { auth, logout } = useAuth()

  return (
    <header className="fixed top-0 left-[240px] right-0 h-14 bg-white border-b border-[#E5E7EB] flex items-center justify-end px-6 gap-4 z-20">
      <span className="font-semibold text-sm text-[#111827]">{auth.user?.tenant_name}</span>
      <span className="text-sm text-[#6B7280]">{auth.user?.email}</span>
      <button
        onClick={logout}
        className="text-sm text-[#DC2626] hover:underline"
      >
        Sign out
      </button>
    </header>
  )
}
