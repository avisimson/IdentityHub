import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { CreateKeyDialog } from "../CreateKeyDialog";
import { server } from "@/test/mocks/server";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

describe("CreateKeyDialog", () => {
  it("renders name input and create button", async () => {
    const user = userEvent.setup();
    render(<CreateKeyDialog />);

    await user.click(screen.getByRole("button", { name: /generate api key/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/key name/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^create$/i })).toBeInTheDocument();
    });
  });

  it("validates name required", async () => {
    const user = userEvent.setup();
    render(<CreateKeyDialog />);

    await user.click(screen.getByRole("button", { name: /generate api key/i }));
    await waitFor(() => screen.getByRole("button", { name: /^create$/i }));

    await user.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    });
  });

  it("validates name max 100", async () => {
    const user = userEvent.setup();
    render(<CreateKeyDialog />);

    await user.click(screen.getByRole("button", { name: /generate api key/i }));
    await waitFor(() => screen.getByLabelText(/key name/i));

    await user.type(screen.getByLabelText(/key name/i), "x".repeat(101));
    await user.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(screen.getByText(/under 100/i)).toBeInTheDocument();
    });
  });

  it("submits and shows key reveal card", async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/api-keys`, () =>
        HttpResponse.json(
          {
            id: "key-new",
            name: "Test Key",
            key: "ihub_live_abc123def456abc123def456abc123def456abc123def456",
            created_at: "2026-04-08T10:00:00Z",
          },
          { status: 201 },
        ),
      ),
    );

    render(<CreateKeyDialog />);

    await user.click(screen.getByRole("button", { name: /generate api key/i }));
    await waitFor(() => screen.getByLabelText(/key name/i));

    await user.type(screen.getByLabelText(/key name/i), "Test Key");
    await user.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(screen.getByText(/will only be displayed once/i)).toBeInTheDocument();
    });
  });

  it("shows loading state during creation", async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/api-keys`, async () => {
        await new Promise((r) => setTimeout(r, 200));
        return HttpResponse.json(
          { id: "k", name: "K", key: "ihub_live_xxx", created_at: "2026-01-01T00:00:00Z" },
          { status: 201 },
        );
      }),
    );

    render(<CreateKeyDialog />);
    await user.click(screen.getByRole("button", { name: /generate api key/i }));
    await waitFor(() => screen.getByLabelText(/key name/i));

    await user.type(screen.getByLabelText(/key name/i), "Loading Test");
    await user.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /^create$/i })).toBeDisabled();
    });
  });
});
