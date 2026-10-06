import axios from "axios";
import { useAuthStore } from "../store";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
});

apiClient.interceptors.request.use((config) => {
  const key = useAuthStore.getState().apiKey;
  if (key) config.headers.set("X-API-Key", key);
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error?.response?.status === 401 && window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
    return Promise.reject(error);
  },
);
