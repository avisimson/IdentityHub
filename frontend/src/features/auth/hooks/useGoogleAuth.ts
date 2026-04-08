const GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";

function getRedirectUri() {
  return `${window.location.origin}/auth/google/callback`;
}

export function useGoogleAuth() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  function redirectToGoogle() {
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: getRedirectUri(),
      response_type: "code",
      scope: "openid email profile",
      access_type: "offline",
      prompt: "consent",
    });

    window.location.href = `${GOOGLE_AUTH_URL}?${params.toString()}`;
  }

  return { redirectToGoogle };
}
