import { JiraStatusCard } from "@/features/jira/components/JiraStatusCard";

export function JiraSettingsPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Jira Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your Jira integration
        </p>
      </div>
      <JiraStatusCard />
    </div>
  );
}
