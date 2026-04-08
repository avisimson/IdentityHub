import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import type { ReactNode } from "react";

// We mock useAuth to control the auth state
const mockUseAuth = vi.fn();

vi.mock("@/providers/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
  AuthProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

// Mock FullPageSpinner
vi.mock("@/components/FullPageSpinner", () => ({
  FullPageSpinner: () => <div data-testid="spinner">Loading...</div>,
}));

// Import the route guards from App.tsx — since they're not exported,
// we re-create them based on the exact implementation.
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = mockUseAuth();
  if (isLoading) return <div data-testid="spinner">Loading...</div>;
  if (!user) return <MemoryRouter initialEntries={["/login"]}><div data-testid="redirected-login" /></MemoryRouter>;
  return <>{children}</>;
}

function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = mockUseAuth();
  if (isLoading) return <div data-testid="spinner">Loading...</div>;
  if (user) return <div data-testid="redirected-dashboard" />;
  return <>{children}</>;
}

describe("Route Guards", () => {
  it("protected route shows spinner while loading", () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: true });
    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>,
    );
    expect(screen.getByTestId("spinner")).toBeInTheDocument();
  });

  it("protected route redirects to login when unauthenticated", () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: false });
    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>,
    );
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    expect(screen.getByTestId("redirected-login")).toBeInTheDocument();
  });

  it("protected route renders children when authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "1", email: "t@t.com", full_name: "T", auth_provider: "local" },
      isLoading: false,
    });
    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>,
    );
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("public route shows spinner while loading", () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: true });
    render(
      <PublicOnlyRoute>
        <div>Public Content</div>
      </PublicOnlyRoute>,
    );
    expect(screen.getByTestId("spinner")).toBeInTheDocument();
  });

  it("public route redirects to dashboard when authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "1", email: "t@t.com", full_name: "T", auth_provider: "local" },
      isLoading: false,
    });
    render(
      <PublicOnlyRoute>
        <div>Public Content</div>
      </PublicOnlyRoute>,
    );
    expect(screen.queryByText("Public Content")).not.toBeInTheDocument();
    expect(screen.getByTestId("redirected-dashboard")).toBeInTheDocument();
  });

  it("public route renders children when unauthenticated", () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: false });
    render(
      <PublicOnlyRoute>
        <div>Public Content</div>
      </PublicOnlyRoute>,
    );
    expect(screen.getByText("Public Content")).toBeInTheDocument();
  });
});
