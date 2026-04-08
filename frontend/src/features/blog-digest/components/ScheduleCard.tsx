import { useState, useEffect } from "react";
import { Clock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useBlogDigestSchedule,
  useUpdateSchedule,
} from "@/features/blog-digest/hooks/useBlogDigest";
import { cn } from "@/lib/utils";

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Berlin",
  "Asia/Jerusalem",
  "Asia/Tokyo",
];

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const MINUTES = [0, 15, 30, 45];

function pad(n: number) {
  return n.toString().padStart(2, "0");
}

export function ScheduleCard() {
  const { data: schedule, isLoading } = useBlogDigestSchedule();
  const updateMutation = useUpdateSchedule();

  const [hour, setHour] = useState(9);
  const [minute, setMinute] = useState(0);
  const [timezone, setTimezone] = useState("UTC");
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (schedule) {
      setHour(schedule.hour);
      setMinute(schedule.minute);
      setTimezone(schedule.timezone);
      setEnabled(schedule.enabled);
    }
  }, [schedule]);

  function handleSave() {
    updateMutation.mutate({ hour, minute, timezone, enabled });
  }

  if (isLoading) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-56" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Schedule</CardTitle>
        <CardDescription>
          Configure when the blog digest runs automatically.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Enable toggle */}
        <div className="flex items-center justify-between">
          <Label htmlFor="digest-enabled">Enable scheduled digest</Label>
          <button
            id="digest-enabled"
            type="button"
            role="switch"
            aria-checked={enabled}
            onClick={() => setEnabled((v) => !v)}
            className={cn(
              "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              enabled ? "bg-primary" : "bg-input",
            )}
          >
            <span
              className={cn(
                "pointer-events-none block size-5 rounded-full bg-background shadow-lg ring-0 transition-transform",
                enabled ? "translate-x-5" : "translate-x-0",
              )}
            />
          </button>
        </div>

        {/* Time & timezone selects */}
        <div
          className={cn(
            "space-y-4 transition-opacity",
            !enabled && "pointer-events-none opacity-50",
          )}
        >
          <div className="flex items-center gap-3">
            <div className="space-y-1.5">
              <Label>Hour</Label>
              <Select value={hour} onValueChange={(v) => v != null && setHour(v)}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {HOURS.map((h) => (
                    <SelectItem key={h} value={h}>
                      {pad(h)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <span className="mt-7 text-lg font-medium text-muted-foreground">
              :
            </span>

            <div className="space-y-1.5">
              <Label>Minute</Label>
              <Select
                value={minute}
                onValueChange={(v) => v != null && setMinute(v)}
              >
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MINUTES.map((m) => (
                    <SelectItem key={m} value={m}>
                      {pad(m)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="ml-2 space-y-1.5">
              <Label>Timezone</Label>
              <Select value={timezone} onValueChange={(v) => v && setTimezone(v)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEZONES.map((tz) => (
                    <SelectItem key={tz} value={tz}>
                      {tz}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Save button */}
        <div className="flex justify-end">
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <Clock className="mr-2 size-4" />
            )}
            Save Schedule
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
