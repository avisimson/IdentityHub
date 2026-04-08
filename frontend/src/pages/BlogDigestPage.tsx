import { ManualTriggerCard } from "@/features/blog-digest/components/ManualTriggerCard";
import { ScheduleCard } from "@/features/blog-digest/components/ScheduleCard";

export function BlogDigestPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Blog Digest</h1>
        <p className="text-sm text-muted-foreground">
          Manage automated NHI blog digests
        </p>
      </div>
      <ManualTriggerCard />
      <ScheduleCard />
    </div>
  );
}
