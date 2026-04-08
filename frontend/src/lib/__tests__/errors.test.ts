import { describe, it, expect } from "vitest";
import { AxiosError, type AxiosResponse } from "axios";
import { getErrorMessage, getErrorCode } from "../errors";

function makeAxiosError(
  status: number,
  data?: Record<string, unknown>,
): AxiosError {
  const response = {
    status,
    data: data ?? {},
    statusText: "Error",
    headers: {},
    config: { headers: {} },
  } as unknown as AxiosResponse;

  const error = new AxiosError("Request failed", "ERR_BAD_RESPONSE", undefined, undefined, response);
  return error;
}

describe("getErrorMessage", () => {
  it("429 returns rate limit message", () => {
    const error = makeAxiosError(429, { detail: "Rate limited", code: "RATE_LIMITED" });
    expect(getErrorMessage(error)).toBe("Too many requests. Please wait a moment and try again.");
  });

  it("502 returns jira unavailable message", () => {
    const error = makeAxiosError(502, { code: "JIRA_API_ERROR" });
    expect(getErrorMessage(error)).toBe("Jira is temporarily unavailable. Please try again.");
  });

  it("string detail returns detail", () => {
    const error = makeAxiosError(409, { detail: "Email already registered" });
    expect(getErrorMessage(error)).toBe("Email already registered");
  });

  it("array detail returns validation message", () => {
    const error = makeAxiosError(422, { detail: [{ loc: ["body", "email"], msg: "invalid" }] });
    expect(getErrorMessage(error)).toBe("Validation error. Please check your input.");
  });

  it("unknown error returns fallback", () => {
    const error = new Error("Something broke");
    expect(getErrorMessage(error)).toBe("An unexpected error occurred.");
  });

  it("no response data returns fallback", () => {
    const error = new AxiosError("Network Error", "ERR_NETWORK");
    expect(getErrorMessage(error)).toBe("An unexpected error occurred.");
  });
});

describe("getErrorCode", () => {
  it("extracts code from response", () => {
    const error = makeAxiosError(409, { detail: "Email exists", code: "EMAIL_EXISTS" });
    expect(getErrorCode(error)).toBe("EMAIL_EXISTS");
  });

  it("returns null for missing code", () => {
    const error = makeAxiosError(500, { detail: "Server error" });
    expect(getErrorCode(error)).toBeNull();
  });

  it("returns null for non-axios error", () => {
    const error = new Error("Not an axios error");
    expect(getErrorCode(error)).toBeNull();
  });
});
