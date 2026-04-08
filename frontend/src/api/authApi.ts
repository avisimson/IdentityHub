import api from "./client";
import type { AuthResponse, User } from "@/types";

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface GoogleAuthRequest {
  code: string;
  redirect_uri: string;
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const { data: res } = await api.post<AuthResponse>("/auth/register", data);
  return res;
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const { data: res } = await api.post<AuthResponse>("/auth/login", data);
  return res;
}

export async function googleAuth(
  data: GoogleAuthRequest,
): Promise<AuthResponse> {
  const { data: res } = await api.post<AuthResponse>("/auth/google", data);
  return res;
}

export async function refresh(): Promise<AuthResponse> {
  const { data: res } = await api.post<AuthResponse>("/auth/refresh");
  return res;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}
