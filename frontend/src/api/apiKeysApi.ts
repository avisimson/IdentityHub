import api from "./client";
import type { ApiKey, ApiKeyCreated } from "@/types";

export interface CreateApiKeyRequest {
  name: string;
}

export interface ApiKeysListResponse {
  api_keys: ApiKey[];
}

export async function createKey(
  data: CreateApiKeyRequest,
): Promise<ApiKeyCreated> {
  const { data: res } = await api.post<ApiKeyCreated>("/api-keys", data);
  return res;
}

export async function listKeys(): Promise<ApiKeysListResponse> {
  const { data } = await api.get<ApiKeysListResponse>("/api-keys");
  return data;
}

export async function deleteKey(
  keyId: string,
): Promise<{ detail: string }> {
  const { data } = await api.delete<{ detail: string }>(`/api-keys/${keyId}`);
  return data;
}
