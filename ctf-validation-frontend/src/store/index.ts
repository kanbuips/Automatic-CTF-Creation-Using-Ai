import { create } from "zustand";

interface AuthState {
  apiKey: string;
  setApiKey: (key: string) => void;
}

const KEY = "ctf_api_key";
const read = () => {
  try {
    return localStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
};

export const useAuthStore = create<AuthState>((set) => ({
  apiKey: read(),
  setApiKey: (apiKey) => {
    try {
      localStorage.setItem(KEY, apiKey);
    } catch {
      /* storage unavailable */
    }
    set({ apiKey });
  },
}));
