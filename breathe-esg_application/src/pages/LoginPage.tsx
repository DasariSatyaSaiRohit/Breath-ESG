import React, { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'

export function LoginPage() {
  const { auth, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (auth.accessToken) return <Navigate to="/" replace />

  const handleSubmit = async () => {
    if (!email || !password) { setError('Email and password are required'); return }
    setLoading(true)
    setError('')
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F3F4F6] flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white border border-[#E5E7EB] rounded-xl shadow-sm p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-[#16A34A]">Breathe ESG</h1>
          <p className="text-sm text-[#6B7280] mt-1">Sign in to your account</p>
        </div>

        <div className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        {error && (
          <p className="text-sm text-[#DC2626] text-center">{error}</p>
        )}

        <Button
          variant="primary"
          onClick={handleSubmit}
          loading={loading}
          className="w-full"
        >
          Sign in
        </Button>
      </div>
    </div>
  )
}
