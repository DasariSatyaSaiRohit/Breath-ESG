import axios from 'axios'
import { accessTokenRef } from '../context/AuthContext'

const axiosInstance = axios.create({
  baseURL: '/api/',
  withCredentials: true, // send httpOnly refresh cookie
})

// Request interceptor: attach Bearer token
axiosInstance.interceptors.request.use(config => {
  const token = accessTokenRef.current
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

// Response interceptor: handle 401
axiosInstance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        return new Promise(resolve => {
          subscribeTokenRefresh(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(axiosInstance(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const { data } = await axios.post('/api/auth/refresh/', {}, { withCredentials: true })
        const newToken: string = data.access_token
        accessTokenRef.current = newToken
        onTokenRefreshed(newToken)
        isRefreshing = false
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return axiosInstance(originalRequest)
      } catch {
        isRefreshing = false
        accessTokenRef.current = null
        // Trigger logout by dispatching a custom event — AuthProvider listens
        window.dispatchEvent(new Event('auth:logout'))
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default axiosInstance
