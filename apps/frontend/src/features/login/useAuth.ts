"use client";

import {
  meApiV1AuthMeGetOptions,
  logoutApiV1AuthLogoutPostMutation,
} from "@/client/gen/@tanstack/react-query.gen";
import { useQueryClient, useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ROUTES } from "@/shared/routes";

/**
 * 비인증 컨텍스트(public 페이지)에서 로그인 여부에 따라 UI를 분기할 때 사용.
 * (authed) 하위에서는 useAuthSuspense를 사용한다.
 */
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
      router.push(ROUTES.LOGIN);
    },
  });

  const logout = () => logoutMutation.mutate({});

  return { user, isLoggedIn, isLoading, isError, logout };
}
