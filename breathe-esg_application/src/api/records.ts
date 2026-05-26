import axiosInstance from './axios'
import {
  EsgRecord,
  PaginatedRecordsResponse,
  RecordFilters,
  RecordStatus,
  PatchRecordPayload,
} from '../types'

export async function getRecords(
  filters: RecordFilters
): Promise<PaginatedRecordsResponse> {
  const params: Record<string, string | number> = {}
  if (filters.source)    params.source    = filters.source
  if (filters.status)    params.status    = filters.status
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to)   params.date_to   = filters.date_to
  if (filters.page)      params.page      = filters.page
  const { data } = await axiosInstance.get('records/', { params })
  return data
}

export async function patchRecord(
  id: string,
  payload: PatchRecordPayload
): Promise<EsgRecord> {
  // id is always the prefixed string e.g. "utility_42"
  // payload never includes raw_data
  const { data } = await axiosInstance.patch(`records/${id}/`, payload)
  return data
}

export async function approveRecord(
  id: string
): Promise<{ id: string; status: RecordStatus; approved_by: string; approved_at: string }> {
  const { data } = await axiosInstance.post(`records/${id}/approve/`)
  return data
}

export async function flagRecord(
  id: string,
  reason: string
): Promise<{ id: string; status: RecordStatus; flag_reason: string }> {
  const { data } = await axiosInstance.post(`records/${id}/flag/`, { reason })
  return data
}

export async function bulkApprove(
  ids: string[]
): Promise<{ approved_count: number; failed_ids: string[] }> {
  // ids are prefixed strings
  const { data } = await axiosInstance.post('records/bulk-approve/', { ids })
  return data
}

export async function lockRecords(
  ids: string[]
): Promise<{ locked_count: number; already_locked_count: number }> {
  // ids are prefixed strings
  const { data } = await axiosInstance.post('records/lock/', { ids })
  return data
}
