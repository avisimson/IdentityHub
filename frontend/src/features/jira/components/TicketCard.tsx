import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Ticket } from "@/types";

interface TicketCardProps {
  ticket: Ticket;
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function TicketCard({ ticket }: TicketCardProps) {
  return (
    <a
      href={ticket.jira_ticket_url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-center gap-3 rounded-xl border p-3.5 transition-all duration-150 hover:border-border/80 hover:bg-muted/50 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="shrink-0 font-mono text-xs font-semibold">
            {ticket.jira_ticket_key}
          </Badge>
          <span className="truncate text-sm font-medium">{ticket.summary}</span>
        </div>
        <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
          <time>{formatRelativeTime(ticket.created_at)}</time>
          {ticket.source !== "ui" && (
            <Badge variant="outline" className="text-[0.6rem]">
              via {ticket.source === "api" ? "API" : "Blog Digest"}
            </Badge>
          )}
        </div>
      </div>
      <ExternalLink className="size-4 shrink-0 text-muted-foreground/50 transition-all duration-150 group-hover:text-foreground group-hover:translate-x-0.5" />
    </a>
  );
}
