import { describe, it, expect } from "vitest";
import { queryKeys } from "../queryKeys";

describe("queryKeys", () => {
  it("auth user key", () => {
    expect(queryKeys.auth.user).toEqual(["auth", "user"]);
  });

  it("jira status key", () => {
    expect(queryKeys.jira.status).toEqual(["jira", "status"]);
  });

  it("jira issue types key includes project", () => {
    expect(queryKeys.jira.issueTypes("SEC")).toEqual(["jira", "issueTypes", "SEC"]);
  });

  it("jira tickets key includes project", () => {
    expect(queryKeys.jira.tickets("SEC")).toEqual(["jira", "tickets", "SEC"]);
  });
});
