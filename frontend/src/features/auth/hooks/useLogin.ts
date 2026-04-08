import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { login as loginApi, type LoginRequest } from "@/api/authApi";
import { useAuth } from "@/providers/AuthProvider";

export function useLogin() {
  const { login } = useAuth();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: LoginRequest) => loginApi(data),
    onSuccess: (data) => {
      login(data.access_token, data.user);
      navigate("/dashboard");
    },
  });
}
