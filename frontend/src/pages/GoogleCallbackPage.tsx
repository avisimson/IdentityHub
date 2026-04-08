import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { googleAuth } from "@/api/authApi";
import { useAuth } from "@/providers/AuthProvider";
import { getErrorCode, getErrorMessage } from "@/lib/errors";

export function GoogleCallbackPage() {
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const code = searchParams.get("code");
    if (!code) {
      toast.error("No authorization code received from Google.");
      navigate("/login", { replace: true });
      return;
    }

    async function exchangeCode(authCode: string) {
      try {
        const data = await googleAuth({
          code: authCode,
          redirect_uri: `${window.location.origin}/auth/google/callback`,
        });

        login(data.access_token, data.user);

        const responseCode = (data as unknown as Record<string, unknown>).code;
        if (responseCode === "ACCOUNT_LINKED") {
          toast.info(
            "Your Google account has been linked to your existing account",
          );
        }

        navigate("/dashboard", { replace: true });
      } catch (error) {
        const code = getErrorCode(error);
        if (code === "ACCOUNT_LINKED") {
          toast.info(
            "Your Google account has been linked to your existing account",
          );
        } else {
          toast.error(getErrorMessage(error));
        }
        navigate("/login", { replace: true });
      }
    }

    exchangeCode(code);
  }, [searchParams, login, navigate]);

  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <Loader2 className="size-8 animate-spin text-muted-foreground" />
      <p className="text-sm text-muted-foreground">
        Signing in with Google...
      </p>
    </div>
  );
}
