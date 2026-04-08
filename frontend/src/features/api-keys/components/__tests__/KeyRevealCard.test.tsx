import { describe, it, expect, vi } from "vitest";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { KeyRevealCard } from "../KeyRevealCard";

const TEST_KEY = "ihub_live_abc123def456abc123def456abc123def456abc123def456";

describe("KeyRevealCard", () => {
  it("displays raw key in monospace", () => {
    render(<KeyRevealCard rawKey={TEST_KEY} onDone={vi.fn()} />);
    const codeEl = screen.getByText(TEST_KEY);
    expect(codeEl.tagName.toLowerCase()).toBe("code");
  });

  it("shows warning that key will not be shown again", () => {
    render(<KeyRevealCard rawKey={TEST_KEY} onDone={vi.fn()} />);
    expect(screen.getByText(/will only be displayed once/i)).toBeInTheDocument();
  });

  it("copy button copies to clipboard", async () => {
    const user = userEvent.setup();
    const mockWriteText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: mockWriteText },
      writable: true,
      configurable: true,
    });

    render(<KeyRevealCard rawKey={TEST_KEY} onDone={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /copy/i }));

    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith(TEST_KEY);
    });
  });

  it("done button calls onDone", async () => {
    const user = userEvent.setup();
    const onDone = vi.fn();

    render(<KeyRevealCard rawKey={TEST_KEY} onDone={onDone} />);

    const doneButton = screen.getByRole("button", { name: /copied the key/i });
    await user.click(doneButton);

    expect(onDone).toHaveBeenCalledOnce();
  });
});
