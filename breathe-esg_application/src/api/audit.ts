import axiosInstance from './axios'
import { AuditFilters, AuditLog } from '../types'

export interface PaginatedAuditResponse {
  count: number
  next: string | null
  previous: string | null
  results: AuditLog[]
}

export async function getAuditLog(
  filters: AuditFilters
): Promise<PaginatedAuditResponse> {
  const params: Record<string, string | number> = {}
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to)   params.date_to   = filters.date_to
  if (filters.action)    params.action     = filters.action
  if (filters.page)      params.page       = filters.page
  const { data } = await axiosInstance.get('audit/', { params })
  return data
}
