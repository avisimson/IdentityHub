import type { ReactNode } from "react";
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";
import { useAuth } from "@/providers/AuthProvider";
import { AuthProvider } from "@/providers/AuthProvider";
import { QueryProvider } from "@/providers/QueryProvider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { FullPageSpinner } from "@/components/FullPageSpinner";
import { AuthLayout } from "@/layouts/AuthLayout";
import { AppShell } from "@/layouts/AppShell";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { GoogleCallbackPage } from "@/pages/GoogleCallbackPage";
import { Toaster } from "@/components/ui/sonner";
import { DashboardPage } from "@/pages/DashboardPage";
import { JiraCallbackPage } from "@/pages/JiraCallbackPage";
import { JiraSettingsPage } from "@/pages/JiraSettingsPage";
import { ApiKeysPage } from "@/pages/ApiKeysPage";
import { BlogDigestPage } from "@/pages/BlogDigestPage";

// -- Route Guards --

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <FullPageSpinner />;
  if (user) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

// -- Router --

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    element: (
      <PublicOnlyRoute>
        <AuthLayout />
      </PublicOnlyRoute>
    ),
    children: [
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      { path: "auth/google/callback", element: <GoogleCallbackPage /> },
    ],
  },
  {
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { path: "dashboard", element: <DashboardPage /> },
      { path: "jira/connected", element: <JiraCallbackPage /> },
      { path: "settings/jira", element: <JiraSettingsPage /> },
      { path: "settings/api-keys", element: <ApiKeysPage /> },
      { path: "settings/blog-digest", element: <BlogDigestPage /> },
    ],
  },
]);

function AppRouter() {
  return <RouterProvider router={router} />;
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <AuthProvider>
          <AppRouter />
          <Toaster />
        </AuthProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
}
