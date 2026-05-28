import axiosInstance from './axios'

export interface DashboardSummary {
  stats: {
    total_records: number
    pending_review: number
    approved: number
    flagged: number
    failed: number
  }
  scope_breakdown: {
    scope_1: number
    scope_2: number
    scope_3: number
  }
  source_breakdown: {
    utility: number
    travel: number
    sap: number
  }
  recent_ingestions: Array<{
    job_id: number
    source: string
    status: string
    row_count: number
    created_at: string
  }>
  monthly_trend: Array<{
    month: string   // "YYYY-MM"
    scope_1: number
    scope_2: number
    scope_3: number
  }>
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await axiosInstance.get('dashboard/summary/')
  return data
}
