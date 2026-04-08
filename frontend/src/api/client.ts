import axios from "axios";
import { toast } from "sonner";
import type { User } from "@/types";

let accessToken: string | null = null;
let onUserUpdate: ((user: User | null) => void) | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setUser(user: User | null) {
  onUserUpdate?.(user);
}

export function clearAuth() {
  accessToken = null;
  onUserUpdate?.(null);
}

/**
 * Wire the AuthProvider's state setter so the interceptor can push
 * user updates without importing React context (avoids circular deps).
 */
export function setOnUserUpdate(callback: (user: User | null) => void) {
  onUserUpdate = callback;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const url: string = error.config?.url ?? "";
    const isRefresh = url.includes("/auth/refresh");

    if (error.response?.status === 429 || error.response?.data?.code === "RATE_LIMITED") {
      if (!isRefresh) {
        toast.warning("Too many requests. Please wait a moment.");
      }
    }

    const original = error.config;
    if (error.response?.status === 401 && !original._retry && !isRefresh) {
      original._retry = true;
      try {
        const { data } = await api.post("/auth/refresh");
        setAccessToken(data.access_token);
        setUser(data.user);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        clearAuth();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
