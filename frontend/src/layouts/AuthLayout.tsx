import { Outlet } from "react-router-dom";
import { Shield } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-muted/30 via-background to-muted/50 px-4 py-8">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center gap-3">
          <div className="flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
            <Shield className="size-7" />
          </div>
          <div className="space-y-1 text-center">
            <h1 className="text-2xl font-bold tracking-tight">IdentityHub</h1>
            <p className="text-sm text-muted-foreground">
              Non-Human Identity Management
            </p>
          </div>
        </div>

        <Card className="shadow-sm">
          <CardContent className="pt-6">
            <Outlet />
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground/60">
          Secure NHI lifecycle management for your organization
        </p>
      </div>
    </div>
  );
}
