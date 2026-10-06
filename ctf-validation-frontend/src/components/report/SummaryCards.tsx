import type { Report } from "../../types";
import Badge from "../common/Badge";

const TONE = { pass: "pass", review: "warning", fail: "error" } as const;

export default function SummaryCards({ report }: { report: Report }) {
  const items: [string, React.ReactNode][] = [
    ["Verdict", <Badge key="v" tone={TONE[report.verdict]}>{report.verdict}</Badge>],
    ["Part", report.part_name ?? "-"],
    ["Model", report.model_name ?? "-"],
    ["Template", report.template_version ?? "-"],
    ["Characteristics", report.characteristic_count],
    ["Findings", report.counts.total ?? 0],
    ["Approval", report.approval_status],
  ];
  return (
    <div className="cards">
      {items.map(([label, value]) => (
        <div className="card" key={label}><small className="muted">{label}</small><div>{value}</div></div>
      ))}
    </div>
  );
}
