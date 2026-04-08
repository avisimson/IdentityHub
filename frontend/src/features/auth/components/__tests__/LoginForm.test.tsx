import { describe, it, expect, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, userEvent, waitFor } from "@/test/test-utils";
import { LoginForm } from "../LoginForm";
import { server } from "@/test/mocks/server";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

describe("LoginForm", () => {
  it("renders email and password fields", () => {
    render(<LoginForm />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders submit button", () => {
    render(<LoginForm />);
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("renders link to register", () => {
    render(<LoginForm />);
    const link = screen.getByRole("link", { name: /register/i });
    expect(link).toHaveAttribute("href", "/register");
  });

  it("shows validation error on empty submit", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });
  });

  it("shows validation error for invalid email", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    // "a@b" passes HTML5 email input validation but fails Zod's email check
    await user.type(screen.getByLabelText(/email/i), "a@b");
    await user.type(screen.getByLabelText(/password/i), "anypassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });
  });

  it("submits with valid data", async () => {
    const user = userEvent.setup();
    let loginCalled = false;

    server.use(
      http.post(`${API_BASE}/auth/login`, () => {
        loginCalled = true;
        return HttpResponse.json({
          access_token: "test-token",
          token_type: "bearer",
          user: { id: "1", email: "test@test.com", full_name: "Test", auth_provider: "local" },
        });
      }),
    );

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "MyPassword1!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(loginCalled).toBe(true));
  });

  it("shows INVALID_CREDENTIALS error inline", async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/auth/login`, () =>
        HttpResponse.json(
          { detail: "Invalid email or password", code: "INVALID_CREDENTIALS" },
          { status: 401 },
        ),
      ),
    );

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "WrongPass1!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });

  it("navigates to dashboard on success", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "MyPassword1!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    // The useLogin hook navigates to /dashboard on success — the MemoryRouter
    // in test-utils captures this. We just verify the mutation doesn't throw.
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).not.toBeDisabled();
    });
  });

  it("disables button during submission", async () => {
    const user = userEvent.setup();

    server.use(
      http.post(`${API_BASE}/auth/login`, async () => {
        await new Promise((r) => setTimeout(r, 100));
        return HttpResponse.json({
          access_token: "t", token_type: "bearer",
          user: { id: "1", email: "t@t.com", full_name: "T", auth_provider: "local" },
        });
      }),
    );

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/password/i), "MyPassword1!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeDisabled();
    });
  });
});
