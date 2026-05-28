export interface TenantConfig {
  id: number
  name: string
  timezone: string            // IANA, e.g. "Asia/Kolkata", "America/New_York"
  date_display_format: string // e.g. "DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"
}

export interface AuthUser {
  email: string
  tenant_name: string
  role?: 'admin' | 'analyst'
}

export interface AuthState {
  accessToken: string | null
  user: AuthUser | null
}

export type SourceType =
  | 'utility_electricity'
  | 'travel_air'
  | 'travel_hotel'
  | 'travel_ground'
  | 'travel_rail'
  | 'sap_procurement'

export type RecordStatus = 'pending' | 'approved' | 'flagged' | 'failed'
export type Scope        = 'scope_1' | 'scope_2' | 'scope_3'
export type TravelType   = 'air' | 'hotel' | 'car' | 'rail'
export type RecordPrefix = 'utility' | 'travel' | 'sap'

export type AuditAction =
  | 'created'
  | 'edited'
  | 'approved'
  | 'flagged'
  | 'bulk_approved'
  | 'locked'

export interface EsgRecord {
  id: string                        // prefixed: "utility_42", "travel_7", "sap_5"
  source_type: RecordPrefix         // 'utility' | 'travel' | 'sap'
  travel_type?: TravelType          // only present on travel records
  scope: Scope
  schema_type: string
  activity_date: string
  normalized_value: string | null
  normalized_unit: string
  description: string
  raw_data: Record<string, string>  // keys from source — drives table headers
  status: RecordStatus
  flag_reason: string | null
  is_locked: boolean
  is_duplicate: boolean             // E11b
  edited_by: string | null
  edited_at: string | null
  approved_by: string | null
  approved_at: string | null
  created_at: string
}

export interface PaginatedRecordsResponse {
  count: number
  next: string | null
  previous: string | null
  columns: string[]     // union of raw_data keys for current page — drives headers
  results: EsgRecord[]
}

export type JobStatus = 'pending' | 'running' | 'done' | 'failed'
export type SourceTypeLabel = 'utility_csv' | 'travel_api' | 'travel_csv' | 'sap_csv'

export interface IngestionJob {
  job_id: string
  status: JobStatus
  records_total: number
  records_success: number
  records_failed: number
  error_message: string | null
}

export interface AuditLog {
  id: number
  user: string
  action: AuditAction
  record_source_type: RecordPrefix | null
  record_id: number | null
  job_id: number | null
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  timestamp: string
  ip_address: string | null
}

export interface RecordFilters {
  source?: SourceType | ''
  status?: RecordStatus | ''
  date_from?: string
  date_to?: string
  page?: number
}

export interface AuditFilters {
  date_from?: string
  date_to?: string
  action?: AuditAction | ''
  page?: number
}

export interface PatchRecordPayload {
  normalized_value?: string
  normalized_unit?: string
  description?: string
  flag_reason?: string
  // raw_data intentionally excluded — read-only
}

export interface Toast {
  id: string
  type: 'success' | 'error'
  message: string
}
