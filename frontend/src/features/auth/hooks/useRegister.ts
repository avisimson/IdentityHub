import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { register as registerApi, type RegisterRequest } from "@/api/authApi";
import { useAuth } from "@/providers/AuthProvider";

export function useRegister() {
  const { login } = useAuth();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: RegisterRequest) => registerApi(data),
    onSuccess: (data) => {
      login(data.access_token, data.user);
      navigate("/dashboard");
    },
  });
}
