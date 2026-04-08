import { describe, it, expect, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { ApiKeysPage } from "@/pages/ApiKeysPage";
import { server } from "@/test/mocks/server";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

describe("ApiKeysPage Integration", () => {
  it("loading state shows skeletons", () => {
    server.use(
      http.get(`${API_BASE}/api-keys`, async () => {
        await new Promise((r) => setTimeout(r, 10000));
        return HttpResponse.json({ api_keys: [] });
      }),
    );

    render(<ApiKeysPage />);
    const skeletons = document.querySelectorAll("[data-slot='skeleton']");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("empty state shows create CTA", async () => {
    server.use(
      http.get(`${API_BASE}/api-keys`, () =>
        HttpResponse.json({ api_keys: [] }),
      ),
    );

    render(<ApiKeysPage />);

    await waitFor(() => {
      expect(screen.getByText(/no api keys yet/i)).toBeInTheDocument();
    });
  });

  it("displays keys from api", async () => {
    server.use(
      http.get(`${API_BASE}/api-keys`, () =>
        HttpResponse.json({
          api_keys: [
            { id: "k-1", name: "Key One", key_prefix: "ihub_live_aa", created_at: "2026-01-01T00:00:00Z", last_used_at: null },
            { id: "k-2", name: "Key Two", key_prefix: "ihub_live_bb", created_at: "2026-01-01T00:00:00Z", last_used_at: null },
          ],
        }),
      ),
    );

    render(<ApiKeysPage />);

    await waitFor(() => {
      expect(screen.getByText("Key One")).toBeInTheDocument();
      expect(screen.getByText("Key Two")).toBeInTheDocument();
    });
  });

  it("create key flow end to end", async () => {
    const user = userEvent.setup();

    server.use(
      http.get(`${API_BASE}/api-keys`, () =>
        HttpResponse.json({ api_keys: [] }),
      ),
      http.post(`${API_BASE}/api-keys`, () =>
        HttpResponse.json(
          {
            id: "k-new",
            name: "New Key",
            key: "ihub_live_abc123def456abc123def456abc123def456abc123def456",
            created_at: "2026-04-08T10:00:00Z",
          },
          { status: 201 },
        ),
      ),
    );

    render(<ApiKeysPage />);

    await waitFor(() => {
      expect(screen.getByText(/no api keys yet/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /generate api key/i }));

    await waitFor(() => screen.getByLabelText(/key name/i));

    await user.type(screen.getByLabelText(/key name/i), "New Key");
    await user.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(screen.getByText(/will only be displayed once/i)).toBeInTheDocument();
    });
  });

  it("delete key flow end to end", async () => {
    const user = userEvent.setup();
    let deleted = false;

    server.use(
      http.get(`${API_BASE}/api-keys`, () => {
        if (deleted) {
          return HttpResponse.json({ api_keys: [] });
        }
        return HttpResponse.json({
          api_keys: [
            { id: "k-del", name: "Delete Me", key_prefix: "ihub_live_zz", created_at: "2026-01-01T00:00:00Z", last_used_at: null },
          ],
        });
      }),
      http.delete(`${API_BASE}/api-keys/k-del`, () => {
        deleted = true;
        return HttpResponse.json({ detail: "Deleted" });
      }),
    );

    render(<ApiKeysPage />);

    await waitFor(() => {
      expect(screen.getByText("Delete Me")).toBeInTheDocument();
    });

    const deleteBtn = screen.getByRole("button", { name: /delete/i });
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole("button", { name: /^delete$/i });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.queryByText("Delete Me")).not.toBeInTheDocument();
    });
  });

  it("rate limit shows toast", async () => {
    server.use(
      http.get(`${API_BASE}/api-keys`, () =>
        HttpResponse.json(
          { detail: "Rate limit exceeded. Try again later.", code: "RATE_LIMITED" },
          { status: 429 },
        ),
      ),
    );

    render(<ApiKeysPage />);

    // The axios interceptor shows a toast on 429.
    // We verify the request was made and the component handles the error state.
    await waitFor(() => {
      const errorEl = screen.queryByText(/failed to load/i);
      // The error state OR a toast should appear
      expect(errorEl || document.querySelector("[data-sonner-toast]")).toBeTruthy();
    });
  });
});
