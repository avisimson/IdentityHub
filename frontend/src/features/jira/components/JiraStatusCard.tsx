import { CheckCircle2, XCircle, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useJiraStatus } from "@/features/jira/hooks/useJiraStatus";
import { ConnectJiraButton } from "./ConnectJiraButton";
import { DisconnectJiraButton } from "./DisconnectJiraButton";

export function JiraStatusCard() {
  const { data: status, isLoading, isError, refetch } = useJiraStatus();

  if (isLoading) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Skeleton className="size-5 rounded-full" />
              <Skeleton className="h-4 w-24" />
            </div>
            <Skeleton className="h-9 w-28" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="shadow-sm">
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <AlertCircle className="size-8 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load Jira connection status.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-1.5 size-3" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const isConnected = status?.connected ?? false;

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Jira Connection</CardTitle>
        <CardDescription>
          {isConnected
            ? "Your Jira account is connected and ready to use."
            : "Connect your Atlassian account to create NHI finding tickets."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            {isConnected ? (
              <>
                <div className="flex size-9 items-center justify-center rounded-full bg-green-100 dark:bg-green-950/40">
                  <CheckCircle2 className="size-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="text-sm font-medium">Connected</p>
                  {status?.jira_site_url && (
                    <p className="text-xs text-muted-foreground">
                      {status.jira_site_url}
                    </p>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="flex size-9 items-center justify-center rounded-full bg-muted">
                  <XCircle className="size-5 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">Not connected</p>
              </>
            )}
          </div>
          {isConnected ? <DisconnectJiraButton /> : <ConnectJiraButton />}
        </div>
      </CardContent>
    </Card>
  );
}
