import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Button from "../../components/common/Button";
import Loader from "../../components/common/Loader";
import PageContainer from "../../components/layout/PageContainer";
import AnomalyChart from "../../components/report/AnomalyChart";
import SummaryCards from "../../components/report/SummaryCards";
import FindingsTable from "../../components/validation/FindingsTable";
import { downloadReport, getReport } from "../../services/reportService";
import type { Report } from "../../types";
import { errorMessage } from "../../utils/format";

export default function ReportView() {
  const { id = "" } = useParams();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReport(id).then(setReport).catch((e) => setError(errorMessage(e)));
  }, [id]);

  const download = (fmt: "xlsx" | "pdf") => downloadReport(id, fmt).catch((e) => setError(errorMessage(e)));

  return (
    <PageContainer title="QC report">
      {error && <p className="error-text">{error}</p>}
      {!report ? !error && <Loader /> : (
        <>
          <SummaryCards report={report} />
          <AnomalyChart counts={report.counts} anomalies={report.anomalies} />
          <FindingsTable findings={report.findings} />
          <p>
            <Button variant="secondary" onClick={() => download("xlsx")}>Download Excel</Button>{" "}
            <Button variant="secondary" onClick={() => download("pdf")}>Download PDF</Button>{" "}
            <Link to={`/approval/${id}`}>Review &amp; approve</Link>
          </p>
        </>
      )}
    </PageContainer>
  );
}
