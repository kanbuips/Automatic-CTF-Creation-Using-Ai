import type { Approval } from "../types";
import { apiClient } from "./apiClient";

export const submitApproval = async (
  id: string,
  body: { decision: "approve" | "reject"; comment: string; reviewer: string },
) => (await apiClient.post<Approval>(`/approval/${id}`, body)).data;

export const getApprovals = async (id: string) => (await apiClient.get<Approval[]>(`/approval/${id}`)).data;
