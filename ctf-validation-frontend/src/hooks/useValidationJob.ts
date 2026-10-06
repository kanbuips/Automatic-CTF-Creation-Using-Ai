import { getJob } from "../services/validationService";
import type { JobDetail } from "../types";
import { usePolling } from "./usePolling";

export const useValidationJob = (id: string) =>
  usePolling<JobDetail>(
    () => getJob(id),
    (j) => j.status === "completed" || j.status === "failed",
  );
