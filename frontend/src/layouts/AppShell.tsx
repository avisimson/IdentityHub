import { useState, useEffect, useCallback } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Link as LinkIcon,
  KeyRound,
  Newspaper,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  ChevronDown,
  Shield,
  Menu,
  X,
} from "lucide-react";
import { useAuth } from "@/providers/AuthProvider";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useJiraStatus } from "@/features/jira/hooks/useJiraStatus";

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  section?: string;
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    to: "/dashboard",
    icon: <LayoutDashboard className="size-4" />,
  },
  {
    label: "Jira",
    to: "/settings/jira",
    icon: <LinkIcon className="size-4" />,
    section: "Settings",
  },
  {
    label: "API Keys",
    to: "/settings/api-keys",
    icon: <KeyRound className="size-4" />,
    section: "Settings",
  },
  {
    label: "Blog Digest",
    to: "/settings/blog-digest",
    icon: <Newspaper className="size-4" />,
    section: "Settings",
  },
];

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.innerWidth < breakpoint,
  );

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);

  return isMobile;
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isMobile = useIsMobile();
  const { user, logout } = useAuth();
  const location = useLocation();

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!isMobile) setMobileOpen(false);
  }, [isMobile]);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  let lastSection: string | undefined;

  const sidebarContent = (
    <>
      {/* Sidebar header */}
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
          <Shield className="size-4" />
        </div>
        {(!collapsed || isMobile) && (
          <span className="font-semibold tracking-tight">IdentityHub</span>
        )}
        {isMobile && (
          <Button
            variant="ghost"
            size="icon-sm"
            className="ml-auto"
            onClick={closeMobile}
            aria-label="Close menu"
          >
            <X className="size-4" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {navItems.map((item) => {
          const showSection =
            item.section && item.section !== lastSection;
          if (item.section) lastSection = item.section;

          return (
            <div key={item.to}>
              {showSection && (!collapsed || isMobile) && (
                <p className="mb-1 mt-4 px-3 text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground">
                  {item.section}
                </p>
              )}
              {showSection && collapsed && !isMobile && (
                <Separator className="my-2" />
              )}
              <Tooltip>
                <TooltipTrigger
                  render={
                    <NavLink
                      to={item.to}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/70 transition-all duration-150 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                        location.pathname === item.to &&
                          "bg-sidebar-accent text-sidebar-accent-foreground font-semibold",
                        collapsed && !isMobile && "justify-center px-0",
                      )}
                    />
                  }
                >
                  {item.icon}
                  {(!collapsed || isMobile) && <span>{item.label}</span>}
                </TooltipTrigger>
                {collapsed && !isMobile && (
                  <TooltipContent side="right">
                    {item.label}
                  </TooltipContent>
                )}
              </Tooltip>
            </div>
          );
        })}
      </nav>

      {/* Jira status badge */}
      {(!collapsed || isMobile) && (
        <div className="border-t p-3">
          <JiraStatusBadge />
        </div>
      )}

      {/* Collapse toggle — desktop only */}
      {!isMobile && (
        <div className="border-t p-2">
          <Button
            variant="ghost"
            size="icon"
            className="w-full transition-colors"
            onClick={() => setCollapsed((c) => !c)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <PanelLeft className="size-4" />
            ) : (
              <PanelLeftClose className="size-4" />
            )}
          </Button>
        </div>
      )}
    </>
  );

  return (
    <TooltipProvider>
      <div className="flex min-h-screen bg-background">
        {/* Mobile overlay */}
        {isMobile && mobileOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity"
            onClick={closeMobile}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <aside
          className={cn(
            "flex flex-col border-r bg-sidebar transition-all duration-200 ease-in-out",
            isMobile
              ? cn(
                  "fixed inset-y-0 left-0 z-50 w-64 shadow-xl",
                  mobileOpen
                    ? "translate-x-0"
                    : "-translate-x-full",
                )
              : cn(collapsed ? "w-16" : "w-60"),
          )}
        >
          {sidebarContent}
        </aside>

        {/* Main area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Topbar */}
          <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background/95 px-4 backdrop-blur-sm supports-[backdrop-filter]:bg-background/60 sm:px-6">
            <div className="flex items-center gap-3">
              {isMobile && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => setMobileOpen(true)}
                  aria-label="Open menu"
                >
                  <Menu className="size-5" />
                </Button>
              )}
              <span className="text-sm font-semibold text-foreground">
                IdentityHub
              </span>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm outline-none transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring">
                <Avatar size="sm">
                  <AvatarFallback className="text-[0.6rem]">
                    {user ? getInitials(user.full_name) : "?"}
                  </AvatarFallback>
                </Avatar>
                {user && (
                  <span className="hidden font-medium sm:inline-block">
                    {user.full_name}
                  </span>
                )}
                <ChevronDown className="size-3.5 text-muted-foreground" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" sideOffset={8}>
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{user?.full_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="size-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </header>

          {/* Page content */}
          <main className="flex-1 overflow-y-auto p-4 sm:p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}

function JiraStatusBadge() {
  const { data: jiraStatus, isLoading } = useJiraStatus();
  const connected = jiraStatus?.connected ?? false;

  return (
    <NavLink
      to="/settings/jira"
      className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
    >
      <LinkIcon className="size-3.5" />
      <span>Jira</span>
      {!isLoading && (
        <Badge
          variant={connected ? "secondary" : "outline"}
          className="ml-auto gap-1 text-[0.6rem]"
        >
          <span
            className={cn(
              "inline-block size-1.5 rounded-full",
              connected
                ? "bg-green-500 shadow-[0_0_4px_theme(colors.green.500/0.5)]"
                : "bg-muted-foreground/50",
            )}
          />
          {connected ? "Connected" : "Not Connected"}
        </Badge>
      )}
    </NavLink>
  );
}
