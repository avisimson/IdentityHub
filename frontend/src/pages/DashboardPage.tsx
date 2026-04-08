import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, LinkIcon, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useJiraStatus } from "@/features/jira/hooks/useJiraStatus";
import { ProjectCombobox } from "@/features/jira/components/ProjectCombobox";
import { CreateTicketForm } from "@/features/jira/components/CreateTicketForm";
import { RecentTicketsList } from "@/features/jira/components/RecentTicketsList";

export function DashboardPage() {
  const {
    data: jiraStatus,
    isLoading: isStatusLoading,
    isError,
    refetch,
  } = useJiraStatus();
  const [selectedProjectKey, setSelectedProjectKey] = useState<
    string | undefined
  >();

  if (isStatusLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Skeleton className="h-7 w-36" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-10 w-full" />
        </div>
        <Skeleton className="h-[260px] w-full rounded-xl" />
        <div className="space-y-3">
          <Skeleton className="h-4 w-32" />
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-lg space-y-5 py-24 text-center">
        <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="size-8 text-destructive" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">Unable to load dashboard</h2>
          <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
            Something went wrong while checking your Jira connection. Please
            check your network and try again.
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!jiraStatus?.connected) {
    return (
      <div className="mx-auto max-w-lg space-y-6 py-24 text-center">
        <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-primary/10">
          <LinkIcon className="size-8 text-primary" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">Connect Jira to get started</h2>
          <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
            Link your Atlassian account to create and track NHI finding tickets
            directly from IdentityHub.
          </p>
        </div>
        <Button render={<Link to="/settings/jira" />}>Connect Jira</Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>

      <div className="space-y-2">
        <label className="text-sm font-medium">Project</label>
        <ProjectCombobox
          value={selectedProjectKey}
          onSelect={setSelectedProjectKey}
        />
      </div>

      {selectedProjectKey && (
        <CreateTicketForm projectKey={selectedProjectKey} />
      )}

      <RecentTicketsList projectKey={selectedProjectKey} />
    </div>
  );
}
