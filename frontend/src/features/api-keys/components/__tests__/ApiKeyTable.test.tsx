import { describe, it, expect, vi } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { ApiKeyTable } from "../ApiKeyTable";
import type { ApiKey } from "@/types";

const mockKeys: ApiKey[] = [
  {
    id: "key-1",
    name: "CI Pipeline Key",
    key_prefix: "ihub_live_ab",
    created_at: "2026-03-15T08:00:00Z",
    last_used_at: "2026-04-08T12:00:00Z",
  },
  {
    id: "key-2",
    name: "Scanner Key",
    key_prefix: "ihub_live_cd",
    created_at: "2026-04-01T12:00:00Z",
    last_used_at: null,
  },
];

describe("ApiKeyTable", () => {
  it("renders table with columns", () => {
    render(<ApiKeyTable apiKeys={mockKeys} isLoading={false} />);
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Key")).toBeInTheDocument();
    expect(screen.getByText("Last Used")).toBeInTheDocument();
  });

  it("displays key prefix not full key", () => {
    render(<ApiKeyTable apiKeys={mockKeys} isLoading={false} />);
    expect(screen.getByText(/ihub_live_ab/)).toBeInTheDocument();
    expect(screen.queryByText(/ihub_live_ab.*[a-f0-9]{40}/)).not.toBeInTheDocument();
  });

  it("shows last used relative time", () => {
    render(<ApiKeyTable apiKeys={mockKeys} isLoading={false} />);
    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("delete button shows confirmation", async () => {
    const user = userEvent.setup();
    render(<ApiKeyTable apiKeys={mockKeys} isLoading={false} />);

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });
  });

  it("empty state when no keys", () => {
    render(<ApiKeyTable apiKeys={[]} isLoading={false} />);
    expect(screen.getByText(/no api keys yet/i)).toBeInTheDocument();
  });
});
