import { AlertCircle, Ticket as TicketIcon, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TicketCard } from "./TicketCard";
import { useRecentTickets } from "@/features/jira/hooks/useRecentTickets";

interface RecentTicketsListProps {
  projectKey: string | undefined;
}

export function RecentTicketsList({ projectKey }: RecentTicketsListProps) {
  const { data, isLoading, isError, refetch } = useRecentTickets(projectKey);
  const tickets = data?.tickets ?? [];

  if (!projectKey) return null;

  if (isLoading) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-foreground">Recent Tickets</h3>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 rounded-xl border p-3.5">
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-foreground">Recent Tickets</h3>
        <div className="flex flex-col items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 p-8 text-center">
          <AlertCircle className="size-8 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load recent tickets.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-1.5 size-3" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Recent Tickets</h3>
        {tickets.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {tickets.length} ticket{tickets.length !== 1 && "s"}
          </span>
        )}
      </div>
      {tickets.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-8 text-center">
          <TicketIcon className="size-8 text-muted-foreground/40" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">
              No tickets yet
            </p>
            <p className="text-xs text-muted-foreground/70">
              Create your first NHI finding using the form above
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {tickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}
    </div>
  );
}
