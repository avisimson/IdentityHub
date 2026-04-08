import axios from "axios";

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data;

    if (status === 429) {
      return "Too many requests. Please wait a moment and try again.";
    }
    if (data?.detail) {
      return typeof data.detail === "string"
        ? data.detail
        : "Validation error. Please check your input.";
    }
    if (status === 502) {
      return "Jira is temporarily unavailable. Please try again.";
    }
  }
  return "An unexpected error occurred.";
}

export function getErrorCode(error: unknown): string | null {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.code ?? null;
  }
  return null;
}
