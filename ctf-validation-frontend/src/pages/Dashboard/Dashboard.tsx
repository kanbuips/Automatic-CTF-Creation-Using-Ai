import { Link } from "react-router-dom";
import Badge from "../../components/common/Badge";
import Loader from "../../components/common/Loader";
import Table from "../../components/common/Table";
import PageContainer from "../../components/layout/PageContainer";
import { usePolling } from "../../hooks/usePolling";
import { listJobs } from "../../services/validationService";
import type { Job } from "../../types";
import { formatDate } from "../../utils/format";

const TONE = { pass: "pass", review: "warning", fail: "error" } as const;

export default function Dashboard() {
  const { data: jobs, error } = usePolling<Job[]>(listJobs, (j) => j.every((x) => x.status === "completed" || x.status === "failed"), 4000);
  const count = (v: string) => jobs?.filter((j) => j.verdict === v).length ?? 0;
  return (
    <PageContainer title="Dashboard">
      {error && <p className="error-text">{error}</p>}
      {!jobs ? <Loader /> : (
        <>
          <div className="cards">
            {[["Jobs", jobs.length], ["Pass", count("pass")], ["Review", count("review")], ["Fail", count("fail")]].map(([l, v]) => (
              <div className="card" key={l}><small className="muted">{l}</small><div>{v}</div></div>
            ))}
          </div>
          <Table
            rows={jobs}
            rowKey={(j) => j.id}
            empty="No validations yet"
            columns={[
              { header: "Part", render: (j) => <Link to={`/jobs/${j.id}`}>{j.part_name ?? j.id.slice(0, 8)}</Link> },
              { header: "Status", render: (j) => j.status },
              { header: "Verdict", render: (j) => (j.verdict ? <Badge tone={TONE[j.verdict]}>{j.verdict}</Badge> : "-") },
              { header: "Approval", render: (j) => j.approval_status },
              { header: "Created", render: (j) => formatDate(j.created_at) },
            ]}
          />
        </>
      )}
    </PageContainer>
  );
}
