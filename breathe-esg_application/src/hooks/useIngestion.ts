import { useMutation, useQuery } from '@tanstack/react-query'
import {
  uploadUtilityCSV,
  pullTravel,
  uploadTravelCSV,
  getJob,
} from '../api/ingestion'
import { IngestionJob } from '../types'

export function useUploadUtilityCSV() {
  return useMutation({ mutationFn: (file: File) => uploadUtilityCSV(file) })
}

export function usePullTravel() {
  return useMutation({
    mutationFn: (params: { date_from: string; date_to: string; trip_id?: string }) =>
      pullTravel(params),
  })
}

export function useUploadTravelCSV() {
  return useMutation({ mutationFn: (file: File) => uploadTravelCSV(file) })
}

export function useJobPolling(jobId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId!),
    enabled: enabled && jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'done' || status === 'failed') return false
      return 3000
    },
  })
}
