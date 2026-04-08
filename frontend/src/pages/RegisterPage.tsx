import { RegisterForm } from "@/features/auth/components/RegisterForm";
import { GoogleSignInButton } from "@/features/auth/components/GoogleSignInButton";
import { Separator } from "@/components/ui/separator";

export function RegisterPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="text-lg font-semibold tracking-tight">
          Create an account
        </h2>
        <p className="text-sm text-muted-foreground">
          Get started with IdentityHub
        </p>
      </div>

      <RegisterForm />

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <Separator className="w-full" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-card px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>

      <GoogleSignInButton />
    </div>
  );
}
