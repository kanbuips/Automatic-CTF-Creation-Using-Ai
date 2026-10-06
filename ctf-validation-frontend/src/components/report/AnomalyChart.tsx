import { SEVERITIES } from "../../utils/constants";

/** Findings per severity as horizontal bars, plus the list of anomalous characteristics. */
export default function AnomalyChart({ counts, anomalies }: { counts: Record<string, number>; anomalies: string[] }) {
  const max = Math.max(1, ...SEVERITIES.map((s) => counts[s] ?? 0));
  return (
    <div>
      {SEVERITIES.map((s) => (
        <div className="bar-row" key={s}>
          <span>{s}</span>
          <div className="bar"><div className={`bar-fill badge-${s}`} style={{ width: `${((counts[s] ?? 0) / max) * 100}%` }} /></div>
          <span>{counts[s] ?? 0}</span>
        </div>
      ))}
      <p className="muted">Anomalous characteristics: {anomalies.length ? anomalies.join(", ") : "none"}</p>
    </div>
  );
}
