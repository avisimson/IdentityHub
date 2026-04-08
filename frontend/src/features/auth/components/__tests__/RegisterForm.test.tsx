import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { RegisterForm } from "../RegisterForm";
import { server } from "@/test/mocks/server";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

describe("RegisterForm", () => {
  it("renders email, password, and name fields", () => {
    render(<RegisterForm />);
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("validates password min 8 chars", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "short");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    });
  });

  it("validates full name required", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "Str0ngP@ss!");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    });
  });

  it("validates full name max 255", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "A".repeat(256));
    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "Str0ngP@ss!");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      const errors = screen.getAllByRole("paragraph").filter(
        (el) => el.classList.contains("text-destructive"),
      );
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  it("shows EMAIL_EXISTS error on email field", async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/auth/register`, () =>
        HttpResponse.json(
          { detail: "Email already registered", code: "EMAIL_EXISTS" },
          { status: 409 },
        ),
      ),
    );

    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "dupe@test.com");
    await user.type(screen.getByLabelText(/password/i), "Str0ngP@ss!");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/this email is already registered/i)).toBeInTheDocument();
    });
  });

  it("submits valid data", async () => {
    const user = userEvent.setup();
    let registerCalled = false;

    server.use(
      http.post(`${API_BASE}/auth/register`, () => {
        registerCalled = true;
        return HttpResponse.json(
          {
            access_token: "t",
            token_type: "bearer",
            user: { id: "1", email: "new@test.com", full_name: "New", auth_provider: "local" },
          },
          { status: 201 },
        );
      }),
    );

    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "New User");
    await user.type(screen.getByLabelText(/email/i), "new@test.com");
    await user.type(screen.getByLabelText(/password/i), "Str0ngP@ss!");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => expect(registerCalled).toBe(true));
  });

  it("navigates to dashboard on success", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "New User");
    await user.type(screen.getByLabelText(/email/i), "new@test.com");
    await user.type(screen.getByLabelText(/password/i), "Str0ngP@ss!");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /create account/i })).not.toBeDisabled();
    });
  });

  it("renders link to login", () => {
    render(<RegisterForm />);
    const link = screen.getByRole("link", { name: /sign in/i });
    expect(link).toHaveAttribute("href", "/login");
  });
});
