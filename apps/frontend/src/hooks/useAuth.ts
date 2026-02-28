"use client";

import { useQueryClient, useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  meApiV1AuthMeGetOptions,
  logoutApiV1AuthLogoutPostMutation,
} from "@/client/gen";

export function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const { data, isLoading, isError } = useQuery({
    ...meApiV1AuthMeGetOptions(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const user = data?.data ?? null;
  const isLoggedIn = !!user;

  const logoutMutation = useMutation({
    ...logoutApiV1AuthLogoutPostMutation(),
    onSuccess: () => {
      queryClient.clear();
      router.push("/login");
    },
  });

  const logout = () => logoutMutation.mutate({});

  return { user, isLoggedIn, isLoading, isError, logout };
}
