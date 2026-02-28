"use client";

import { useTransition } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  guestLoginApiV1AuthGuestLoginPostMutation,
  meApiV1AuthMeGetQueryKey,
} from "@/client/gen";
import type { GuestInfo } from "@/client/gen";
import { toast } from "sonner";
import {
  LoginFormValues,
  loginSchema,
  LOGIN_DEFAULT_VALUES,
} from "./login-schema";

function getPostLoginPath(user: GuestInfo) {
  switch (user.in_case) {
    case true:
      return `/case/${user.current_case_id}`;
    default:
      return "/rooms";
  }
}

export function LoginForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isNavigating, startTransition] = useTransition();

  const { control, handleSubmit } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: LOGIN_DEFAULT_VALUES,
  });

  const { mutate, isPending } = useMutation({
    ...guestLoginApiV1AuthGuestLoginPostMutation(),
    onSuccess: (data) => {
      queryClient.setQueryData(meApiV1AuthMeGetQueryKey(), data);

      startTransition(() => {
        router.push(getPostLoginPath(data.data!));
      });
    },
    onError: () => {
      toast.error("로그인에 실패했습니다. 다시 시도해주세요.");
    },
  });

  const isDisabled = isPending || isNavigating;

  const onSubmit = ({ username }: LoginFormValues) => {
    mutate({ body: { username } });
  };

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-2xl">로그인</CardTitle>
      </CardHeader>

      <CardContent>
        <form id="login-form" onSubmit={handleSubmit(onSubmit)}>
          <FieldGroup>
            <Controller
              name="username"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <Input
                    {...field}
                    placeholder="닉네임을 입력하세요"
                    disabled={isDisabled}
                    aria-invalid={fieldState.invalid}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
          </FieldGroup>
        </form>
      </CardContent>

      <CardFooter>
        <Button
          className="w-full"
          type="submit"
          form="login-form"
          disabled={isDisabled}
        >
          {isDisabled ? "로그인 중..." : "로그인"}
        </Button>
      </CardFooter>
    </Card>
  );
}
