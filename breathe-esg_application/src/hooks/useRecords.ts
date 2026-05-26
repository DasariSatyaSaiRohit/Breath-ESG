import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getRecords,
  patchRecord,
  approveRecord,
  flagRecord,
  bulkApprove,
  lockRecords,
} from '../api/records'
import { RecordFilters, PatchRecordPayload } from '../types'

const RECORDS_KEY = 'records'

export function useRecordsQuery(filters: RecordFilters) {
  return useQuery({
    queryKey: [RECORDS_KEY, filters],
    queryFn: () => getRecords(filters),
  })
}

export function useApproveRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => approveRecord(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [RECORDS_KEY] }),
  })
}

export function useFlagRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      flagRecord(id, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: [RECORDS_KEY] }),
  })
}

export function usePatchRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: PatchRecordPayload }) =>
      patchRecord(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [RECORDS_KEY] }),
  })
}

export function useBulkApprove() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ids: string[]) => bulkApprove(ids),
    onSuccess: () => qc.invalidateQueries({ queryKey: [RECORDS_KEY] }),
  })
}

export function useLockRecords() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ids: string[]) => lockRecords(ids),
    onSuccess: () => qc.invalidateQueries({ queryKey: [RECORDS_KEY] }),
  })
}
