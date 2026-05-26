import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navItems = [
  {
    to: '/',
    label: 'Dashboard',
    end: true,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    to: '/ingest',
    label: 'Ingest',
    end: false,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
  },
  {
    to: '/review',
    label: 'Review',
    end: false,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
  {
    to: '/audit',
    label: 'Audit Log',
    end: false,
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
]

export function Sidebar() {
  const { auth, logout } = useAuth()

  return (
    <aside className="fixed left-0 top-0 h-full w-[240px] bg-[#F8F9FA] border-r border-[#E5E7EB] flex flex-col z-30">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[#E5E7EB]">
        <p className="text-[16px] font-semibold text-[#16A34A]">Breathe ESG</p>
        <p className="text-[13px] text-[#6B7280] mt-0.5">{auth.user?.tenant_name}</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors
              ${isActive
                ? 'bg-[#E9ECEF] border-l-[3px] border-[#16A34A] text-[#16A34A] font-medium pl-[13px]'
                : 'text-[#6B7280] hover:bg-[#F3F4F6] border-l-[3px] border-transparent pl-[13px]'
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-[#E5E7EB]">
        <p className="text-[12px] text-[#6B7280] truncate">{auth.user?.email}</p>
        <button
          onClick={logout}
          className="mt-1.5 text-[13px] text-[#DC2626] hover:underline"
        >
          Sign out
        </button>
      </div>
    </aside>
  )
}
