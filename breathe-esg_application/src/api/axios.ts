/// <reference types="vite/client" />

/**
 * src/api/axios.ts
 *
 * In production (Railway):
 *   VITE_API_URL=https://your-backend.up.railway.app
 *   axiosInstance.baseURL = 'https://your-backend.up.railway.app/api/'
 *
 * In local dev:
 *   VITE_API_URL is unset → baseURL = '/api/' → Vite proxy forwards to Django
 *
 * withCredentials=true is required for the httpOnly refresh token cookie
 * to be sent cross-origin in production.
 */
import axios from 'axios'
import { accessTokenRef } from '../context/AuthContext'

// Use VITE_API_URL in production; fall back to relative '/api/' for dev proxy
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/`
  : '/api/'

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,  // send httpOnly refresh cookie on every request
})

// ── Request interceptor — attach Bearer token ────────────────────────────────
axiosInstance.interceptors.request.use(config => {
  const token = accessTokenRef.current
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor — handle 401 with silent token refresh ──────────────
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

axiosInstance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        // Queue the request until the ongoing refresh completes
        return new Promise(resolve => {
          subscribeTokenRefresh(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(axiosInstance(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const refreshURL = import.meta.env.VITE_API_URL
          ? `${import.meta.env.VITE_API_URL}/api/auth/refresh/`
          : '/api/auth/refresh/'

        const { data } = await axios.post(refreshURL, {}, { withCredentials: true })
        const newToken: string = data.access_token

        accessTokenRef.current = newToken
        onTokenRefreshed(newToken)
        isRefreshing = false

        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return axiosInstance(originalRequest)
      } catch {
        isRefreshing = false
        accessTokenRef.current = null
        window.dispatchEvent(new Event('auth:logout'))
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default axiosInstance
