import type { Job, JobDetail } from "../types";
import { apiClient } from "./apiClient";

export const startValidation = async (jtxml_file_id: string, ctf_file_id?: string) =>
  (await apiClient.post<Job>("/validate", { jtxml_file_id, ctf_file_id })).data;

export const getJob = async (id: string) => (await apiClient.get<JobDetail>(`/validate/${id}`)).data;
export const listJobs = async () => (await apiClient.get<Job[]>("/validate")).data;
