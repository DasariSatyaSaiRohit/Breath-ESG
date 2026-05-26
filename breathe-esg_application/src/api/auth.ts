import axiosInstance from './axios'
import { AuthUser } from '../types'

export async function loginApi(
  email: string,
  password: string
): Promise<{ access_token: string; user: AuthUser }> {
  const { data } = await axiosInstance.post('auth/login/', { email, password })
  return data
}

export async function refreshTokenApi(): Promise<{ access_token: string }> {
  const { data } = await axiosInstance.post('auth/refresh/')
  return data
}
