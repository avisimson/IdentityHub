import api from "./client";
import type { BlogDigestSchedule, BlogDigestTriggerResult } from "@/types";

export async function triggerDigest(): Promise<BlogDigestTriggerResult> {
  const { data } = await api.post<BlogDigestTriggerResult>(
    "/blog-digest/trigger",
  );
  return data;
}

export async function getSchedule(): Promise<BlogDigestSchedule> {
  const { data } = await api.get<BlogDigestSchedule>("/blog-digest/schedule");
  return data;
}

export async function updateSchedule(
  payload: BlogDigestSchedule,
): Promise<BlogDigestSchedule> {
  const { data } = await api.put<BlogDigestSchedule>(
    "/blog-digest/schedule",
    payload,
  );
  return data;
}
