import { useState } from "react";
import { uploadFile } from "../services/uploadService";
import { startValidation } from "../services/validationService";
import { errorMessage } from "../utils/format";

export function useUpload() {
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Uploads the files, starts validation and returns the new job id (or null on error). */
  async function submit(jtxml: File, ctf?: File | null): Promise<string | null> {
    setBusy(true);
    setError(null);
    setProgress(0);
    try {
      const uploads = ctf ? 2 : 1;
      const j = await uploadFile("jtxml", jtxml, (f) => setProgress(f / uploads));
      const c = ctf ? await uploadFile("ctf", ctf, (f) => setProgress((1 + f) / uploads)) : undefined;
      const job = await startValidation(j.file_id, c?.file_id);
      return job.id;
    } catch (e) {
      setError(errorMessage(e));
      return null;
    } finally {
      setBusy(false);
    }
  }
  return { submit, progress, busy, error };
}
