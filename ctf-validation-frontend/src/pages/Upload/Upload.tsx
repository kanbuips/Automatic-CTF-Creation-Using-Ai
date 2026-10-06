import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import PageContainer from "../../components/layout/PageContainer";
import FileDropzone from "../../components/upload/FileDropzone";
import UploadProgress from "../../components/upload/UploadProgress";
import { useUpload } from "../../hooks/useUpload";

export default function Upload() {
  const [jtxml, setJtxml] = useState<File | null>(null);
  const [ctf, setCtf] = useState<File | null>(null);
  const { submit, progress, busy, error } = useUpload();
  const navigate = useNavigate();

  async function onSubmit() {
    if (!jtxml) return;
    const id = await submit(jtxml, ctf);
    if (id) navigate(`/jobs/${id}`);
  }

  return (
    <PageContainer title="New validation">
      <FileDropzone label="JTXML file (required)" accept=".jtxml,.xml" file={jtxml} onFile={setJtxml} />
      <FileDropzone label="CTF file (optional)" accept=".xlsx,.xlsm,.xls,.csv" file={ctf} onFile={setCtf} />
      {busy && <UploadProgress fraction={progress} />}
      {error && <p className="error-text">{error}</p>}
      <Button disabled={!jtxml || busy} onClick={onSubmit}>Upload &amp; validate</Button>
    </PageContainer>
  );
}
