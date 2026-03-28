"use client";

import {
  meApiV1AuthMeGetOptions,
  logoutApiV1AuthLogoutPostMutation,
} from "@/client/gen/@tanstack/react-query.gen";
import {
  useQueryClient,
  useSuspenseQuery,
  useMutation,
} from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ROUTES } from "@/shared/routes";

export function useAuthSuspense() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const { data } = useSuspenseQuery({
    ...meApiV1AuthMeGetOptions(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const user = data.data!;

  const logoutMutation = useMutation({
    ...logoutApiV1AuthLogoutPostMutation(),
    onSuccess: () => {
      queryClient.clear();
      router.push(ROUTES.LOGIN);
    },
  });

  const logout = () => logoutMutation.mutate({});

  return { user, logout };
}
