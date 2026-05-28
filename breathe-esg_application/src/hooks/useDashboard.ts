import { useQuery } from '@tanstack/react-query'
import { getDashboardSummary } from '../api/dashboard'

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: getDashboardSummary,
    staleTime: 60_000, // 1 minute
  })
}
