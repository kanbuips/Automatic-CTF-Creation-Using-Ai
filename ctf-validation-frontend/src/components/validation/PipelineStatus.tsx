import type { Stage } from "../../types";
import { STAGE_ORDER } from "../../utils/constants";

export default function PipelineStatus({ stages }: { stages: Record<string, Stage> }) {
  return (
    <ol className="pipeline">
      {STAGE_ORDER.map((name) => {
        const s = stages[name] ?? { status: "pending" };
        return (
          <li key={name} className={`stage stage-${s.status}`} title={s.error}>
            <span>{name}</span>
            <small>{s.status}{s.duration_ms != null ? ` · ${s.duration_ms} ms` : ""}</small>
          </li>
        );
      })}
    </ol>
  );
}
