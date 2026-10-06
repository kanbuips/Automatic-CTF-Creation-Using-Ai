export type Severity = "info" | "warning" | "error" | "critical";

export interface Finding {
  id: string;
  rule: string;
  severity: Severity;
  message: string;
  confidence?: number;
}
