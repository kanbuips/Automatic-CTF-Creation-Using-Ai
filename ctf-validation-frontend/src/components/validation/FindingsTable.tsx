import { useState } from "react";
import type { Finding, Severity } from "../../types";
import { SEVERITIES } from "../../utils/constants";
import { formatPercent } from "../../utils/format";
import Table from "../common/Table";
import SeverityChip from "./SeverityChip";

type Row = Omit<Finding, "id"> & { id?: number };

export default function FindingsTable({ findings }: { findings: Row[] }) {
  const [filter, setFilter] = useState<Severity | "all">("all");
  const rows = filter === "all" ? findings : findings.filter((f) => f.severity === filter);
  return (
    <>
      <label className="muted">
        Severity{" "}
        <select value={filter} onChange={(e) => setFilter(e.target.value as Severity | "all")}>
          <option value="all">all</option>
          {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </label>
      <Table
        rows={rows}
        rowKey={(f) => `${f.rule}-${f.characteristic_id}-${f.message}`}
        empty="No findings"
        columns={[
          { header: "Severity", render: (f) => <SeverityChip severity={f.severity} /> },
          { header: "Rule", render: (f) => f.rule },
          { header: "Item", render: (f) => f.characteristic_id ?? "-" },
          { header: "Message", render: (f) => f.message },
          { header: "Source", render: (f) => f.source },
          { header: "Confidence", render: (f) => formatPercent(f.confidence) },
        ]}
      />
    </>
  );
}
