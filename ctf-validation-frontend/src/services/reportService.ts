import type { Report } from "../types";
import { apiClient } from "./apiClient";

export const getReport = async (id: string) => (await apiClient.get<Report>(`/reports/${id}`)).data;

export async function downloadReport(id: string, format: "xlsx" | "pdf") {
  const res = await apiClient.get(`/reports/${id}/download`, { params: { format }, responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `qc-report-${id}.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}
