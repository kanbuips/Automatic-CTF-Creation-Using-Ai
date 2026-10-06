export const formatDate = (iso: string) => new Date(iso + (iso.endsWith("Z") ? "" : "Z")).toLocaleString();
export const formatBytes = (n: number) => (n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} KB`);
export const formatPercent = (v: number | null | undefined) => (v == null ? "" : `${Math.round(v * 100)}%`);
export const errorMessage = (e: unknown): string => {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? String(d)).join("; ");
  return e instanceof Error ? e.message : "Unexpected error";
};
