import { Link, useParams } from "react-router-dom";
import Loader from "../../components/common/Loader";
import PageContainer from "../../components/layout/PageContainer";
import FindingsTable from "../../components/validation/FindingsTable";
import PipelineStatus from "../../components/validation/PipelineStatus";
import { useValidationJob } from "../../hooks/useValidationJob";

export default function ValidationResult() {
  const { jobId = "" } = useParams();
  const { data: job, error } = useValidationJob(jobId);
  return (
    <PageContainer title="Validation result">
      {error && <p className="error-text">{error}</p>}
      {!job ? <Loader /> : (
        <>
          <p>{job.part_name ?? "(unnamed part)"} · template {job.template_version ?? "?"} · <strong>{job.verdict ?? job.status}</strong></p>
          <PipelineStatus stages={job.stages} />
          {job.error && <p className="error-text">{job.error}</p>}
          {job.status === "completed" && (
            <>
              <FindingsTable findings={job.findings} />
              <p><Link to={`/reports/${job.id}`}>Full report</Link> · <Link to={`/approval/${job.id}`}>Review &amp; approve</Link></p>
            </>
          )}
        </>
      )}
    </PageContainer>
  );
}
