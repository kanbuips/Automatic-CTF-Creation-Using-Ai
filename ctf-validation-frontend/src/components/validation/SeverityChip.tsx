import type { Severity } from "../../types";
import Badge from "../common/Badge";

const TONE: Record<Severity, string> = { critical: "critical", error: "error", warning: "warning", info: "info" };

export default function SeverityChip({ severity }: { severity: Severity }) {
  return <Badge tone={TONE[severity]}>{severity}</Badge>;
}
