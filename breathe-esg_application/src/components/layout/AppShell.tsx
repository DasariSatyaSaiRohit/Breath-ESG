import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

export function AppShell() {
  const { auth } = useAuth()

  if (!auth.accessToken) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="min-h-screen bg-[#F3F4F6]">
      <Sidebar />
      <div className="ml-[240px]">
        <TopBar />
        <main className="pt-14 min-h-screen">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
