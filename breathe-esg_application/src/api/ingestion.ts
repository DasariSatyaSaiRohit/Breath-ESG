import axiosInstance from './axios'
import { IngestionJob } from '../types'

export async function uploadUtilityCSV(file: File): Promise<IngestionJob> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await axiosInstance.post('ingestion/utility/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function pullTravel(params: {
  date_from: string
  date_to: string
  trip_id?: string
}): Promise<IngestionJob> {
  const { data } = await axiosInstance.post('ingestion/travel/pull/', params)
  return data
}

export async function uploadTravelCSV(file: File): Promise<IngestionJob> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await axiosInstance.post('ingestion/travel/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function uploadSapCsv(file: File): Promise<IngestionJob> {
  // POST /api/ingestion/sap/upload/
  // multipart/form-data: file
  // Accepts .csv only
  const form = new FormData()
  form.append('file', file)
  const { data } = await axiosInstance.post('ingestion/sap/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getJob(jobId: string): Promise<IngestionJob> {
  const { data } = await axiosInstance.get(`ingestion/jobs/${jobId}/`)
  return data
}
