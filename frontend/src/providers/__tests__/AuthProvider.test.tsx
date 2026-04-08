import { describe, it, expect, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { render, screen, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider, useAuth } from "../AuthProvider";
import { server } from "@/test/mocks/server";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>{children}</MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );
  };
}

function TestConsumer() {
  const { user, isLoading, accessToken, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="user">{user ? user.email : "null"}</span>
      <span data-testid="token">{accessToken ?? "null"}</span>
      <button onClick={() => login("test-token", { id: "1", email: "t@t.com", full_name: "T", auth_provider: "local" })}>
        Login
      </button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("initial state is loading", () => {
    server.use(
      http.post(`${API_BASE}/auth/refresh`, async () => {
        await new Promise((r) => setTimeout(r, 5000));
        return HttpResponse.json({}, { status: 401 });
      }),
    );

    render(<TestConsumer />, { wrapper: createWrapper() });
    expect(screen.getByTestId("loading").textContent).toBe("true");
  });

  it("attempts silent refresh on mount", async () => {
    let refreshCalled = false;
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () => {
        refreshCalled = true;
        return HttpResponse.json({}, { status: 401 });
      }),
    );

    render(<TestConsumer />, { wrapper: createWrapper() });

    await waitFor(() => expect(refreshCalled).toBe(true));
  });

  it("restores user from refresh response", async () => {
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () =>
        HttpResponse.json({
          access_token: "restored-token",
          token_type: "bearer",
          user: { id: "1", email: "restored@test.com", full_name: "Restored", auth_provider: "local" },
        }),
      ),
    );

    render(<TestConsumer />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("user").textContent).toBe("restored@test.com");
    });
  });

  it("sets loading false on refresh failure", async () => {
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () =>
        HttpResponse.json({ detail: "Invalid" }, { status: 401 }),
      ),
    );

    render(<TestConsumer />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
      expect(screen.getByTestId("user").textContent).toBe("null");
    });
  });

  it("login stores token and user", async () => {
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () =>
        HttpResponse.json({}, { status: 401 }),
      ),
    );

    render(<TestConsumer />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });

    await act(async () => {
      screen.getByText("Login").click();
    });

    expect(screen.getByTestId("user").textContent).toBe("t@t.com");
  });

  it("access token in memory not localStorage", async () => {
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () =>
        HttpResponse.json({}, { status: 401 }),
      ),
    );

    // Spy on jsdom's Storage to detect any token persistence
    const setItemSpy = vi.spyOn(Storage.prototype, "setItem");

    render(<TestConsumer />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });

    await act(async () => {
      screen.getByText("Login").click();
    });

    // Token is available in-memory via context
    expect(screen.getByTestId("token").textContent).toBe("test-token");
    // No call to setItem with token-related keys
    const tokenCalls = setItemSpy.mock.calls.filter(
      ([key]) => key === "access_token" || key === "token",
    );
    expect(tokenCalls).toHaveLength(0);

    setItemSpy.mockRestore();
  });

  it("logout clears state and calls api", async () => {
    let logoutCalled = false;

    server.use(
      http.post(`${API_BASE}/auth/refresh`, () =>
        HttpResponse.json({
          access_token: "t",
          token_type: "bearer",
          user: { id: "1", email: "t@t.com", full_name: "T", auth_provider: "local" },
        }),
      ),
      http.post(`${API_BASE}/auth/logout`, () => {
        logoutCalled = true;
        return HttpResponse.json({ detail: "Logged out" });
      }),
    );

    render(<TestConsumer />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("user").textContent).toBe("t@t.com");
    });

    const locationSpy = vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      href: "http://localhost:3000/",
      assign: vi.fn(),
      replace: vi.fn(),
      reload: vi.fn(),
    } as unknown as Location);

    await act(async () => {
      screen.getByText("Logout").click();
    });

    await waitFor(() => expect(logoutCalled).toBe(true));

    locationSpy.mockRestore();
  });
});
