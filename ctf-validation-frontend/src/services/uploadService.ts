import type { UploadResponse } from "../types";
import { apiClient } from "./apiClient";

export async function uploadFile(
  kind: "jtxml" | "ctf",
  file: File,
  onProgress?: (fraction: number) => void,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<UploadResponse>(`/upload/${kind}`, form, {
    onUploadProgress: (e) => e.total && onProgress?.(e.loaded / e.total),
  });
  return data;
}
