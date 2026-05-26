import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './hooks/useToast'
import { AppShell } from './components/layout/AppShell'
import { ToastContainer } from './components/ui/Toast'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { IngestPage } from './pages/IngestPage'
import { ReviewPage } from './pages/ReviewPage'
import { AuditPage } from './pages/AuditPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<AppShell />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/ingest" element={<IngestPage />} />
                <Route path="/review" element={<ReviewPage />} />
                <Route path="/audit" element={<AuditPage />} />
              </Route>
            </Routes>
          </Router>
          <ToastContainer />
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
