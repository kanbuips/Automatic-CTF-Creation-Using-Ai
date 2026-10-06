export type Severity = "critical" | "error" | "warning" | "info";
export type Verdict = "pass" | "review" | "fail";
export type JobStatus = "pending" | "running" | "completed" | "failed";
export type StageStatus = "pending" | "running" | "done" | "failed" | "skipped";

export interface Stage {
  status: StageStatus;
  duration_ms?: number;
  error?: string;
}

export interface UploadResponse {
  file_id: string;
  kind: "jtxml" | "ctf";
  filename: string;
  size: number;
}

export interface Finding {
  id: number;
  rule: string;
  severity: Severity;
  source: "rule" | "ml" | "anomaly";
  characteristic_id: string | null;
  message: string;
  confidence: number | null;
}

export interface Job {
  id: string;
  status: JobStatus;
  verdict: Verdict | null;
  approval_status: "pending" | "approved" | "rejected";
  part_name: string | null;
  model_name: string | null;
  template_version: string | null;
  stages: Record<string, Stage>;
  counts: Partial<Record<Severity | "total", number>>;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobDetail extends Job {
  findings: Finding[];
}

export interface Report {
  job_id: string;
  filename: string;
  generated_at: string;
  part_name: string | null;
  model_name: string | null;
  template_version: string | null;
  characteristic_count: number;
  verdict: Verdict;
  approval_status: string;
  counts: Record<string, number>;
  by_source: Record<string, number>;
  anomalies: string[];
  findings: Omit<Finding, "id">[];
}

export interface Approval {
  id: number;
  job_id: string;
  decision: "approved" | "rejected";
  comment: string;
  reviewer: string;
  created_at: string;
}
