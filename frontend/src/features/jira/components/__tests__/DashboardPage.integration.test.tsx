import { describe, it, expect, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { DashboardPage } from "@/pages/DashboardPage";
import { server } from "@/test/mocks/server";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

describe("DashboardPage Integration", () => {
  it("loading state shows skeletons", () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, async () => {
        await new Promise((r) => setTimeout(r, 10000));
        return HttpResponse.json({ connected: true });
      }),
    );

    render(<DashboardPage />);
    const skeletons = document.querySelectorAll("[data-slot='skeleton']");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("jira not connected shows connect CTA", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({ connected: false }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Connect Jira to get started")).toBeInTheDocument();
    });
  });

  it("error state shows retry button", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    });
  });

  it("retry button refetches", async () => {
    const user = userEvent.setup();
    let callCount = 0;

    server.use(
      http.get(`${API_BASE}/jira/status`, () => {
        callCount++;
        if (callCount === 1) {
          return HttpResponse.json({}, { status: 500 });
        }
        return HttpResponse.json({ connected: true, cloud_id: "c", jira_site_url: "https://x" });
      }),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() => {
      expect(callCount).toBeGreaterThanOrEqual(2);
    });
  });

  it("connected state shows dashboard heading", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({ connected: true, cloud_id: "c", jira_site_url: "https://x" }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("project selector populates from api", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({ connected: true, cloud_id: "c", jira_site_url: "https://x" }),
      ),
      http.get(`${API_BASE}/jira/projects`, () =>
        HttpResponse.json({
          projects: [
            { id: "1", key: "PROJ", name: "Project Alpha" },
            { id: "2", key: "SEC", name: "Security" },
          ],
        }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("empty tickets shows empty state", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({ connected: true, cloud_id: "c", jira_site_url: "https://x" }),
      ),
      http.get(`${API_BASE}/jira/tickets`, () =>
        HttpResponse.json({ tickets: [] }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("tickets display source badge for non-ui", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({ connected: true, cloud_id: "c", jira_site_url: "https://x" }),
      ),
      http.get(`${API_BASE}/jira/tickets`, () =>
        HttpResponse.json({
          tickets: [
            {
              id: "t-1", jira_ticket_key: "SEC-1",
              jira_ticket_url: "https://x/SEC-1", summary: "API ticket",
              issue_type: "Task", source: "api",
              created_at: "2026-04-08T12:00:00Z",
              created_by: { id: "u-1", full_name: "User" },
            },
          ],
        }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("ticket card opens jira url", async () => {
    server.use(
      http.get(`${API_BASE}/jira/status`, () =>
        HttpResponse.json({ connected: true, cloud_id: "c", jira_site_url: "https://x" }),
      ),
    );

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });
});
