import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Button from "../../components/common/Button";
import Table from "../../components/common/Table";
import PageContainer from "../../components/layout/PageContainer";
import { getApprovals, submitApproval } from "../../services/approvalService";
import type { Approval as ApprovalRow } from "../../types";
import { errorMessage, formatDate } from "../../utils/format";

export default function Approval() {
  const { id = "" } = useParams();
  const [history, setHistory] = useState<ApprovalRow[]>([]);
  const [comment, setComment] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => getApprovals(id).then(setHistory).catch((e) => setError(errorMessage(e))), [id]);
  useEffect(() => { load(); }, [load]);

  async function decide(decision: "approve" | "reject") {
    setError(null);
    try {
      await submitApproval(id, { decision, comment, reviewer: reviewer || "anonymous" });
      setComment("");
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  return (
    <PageContainer title="Approval">
      <div className="form">
        <input placeholder="Reviewer" value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
        <textarea placeholder="Comment (required when rejecting)" value={comment} onChange={(e) => setComment(e.target.value)} />
        {error && <p className="error-text">{error}</p>}
        <div>
          <Button onClick={() => decide("approve")}>Approve</Button>{" "}
          <Button variant="danger" onClick={() => decide("reject")}>Reject</Button>
        </div>
      </div>
      <h3>Audit trail</h3>
      <Table
        rows={history}
        rowKey={(a) => a.id}
        empty="No decisions yet"
        columns={[
          { header: "When", render: (a) => formatDate(a.created_at) },
          { header: "Reviewer", render: (a) => a.reviewer },
          { header: "Decision", render: (a) => a.decision },
          { header: "Comment", render: (a) => a.comment },
        ]}
      />
    </PageContainer>
  );
}
