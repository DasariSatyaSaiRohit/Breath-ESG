import { useQuery } from '@tanstack/react-query'
import { getAuditLog } from '../api/audit'
import { AuditFilters } from '../types'

export function useAuditQuery(filters: AuditFilters) {
  return useQuery({
    queryKey: ['audit', filters],
    queryFn: () => getAuditLog(filters),
  })
}
