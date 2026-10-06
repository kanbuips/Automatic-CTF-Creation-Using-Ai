import type { Severity } from "../types";

export const POLL_INTERVAL_MS = 1500;
export const SEVERITIES: Severity[] = ["critical", "error", "warning", "info"];
export const STAGE_ORDER = ["parsing", "features", "rules", "ml", "anomaly", "report"];
