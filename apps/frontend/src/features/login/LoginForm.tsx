"use client";

import { useTransition } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  LoginFormValues,
  loginSchema,
  LOGIN_DEFAULT_VALUES,
} from "./login-schema";
import { guestLoginApiV1AuthGuestLoginPostMutation } from "@/client/gen/@tanstack/react-query.gen";
import { GuestInfo } from "@/client/gen/types.gen";
import { ROUTES } from "@/shared/routes";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/shadcn-ui/ui/card";
import { Field, FieldError, FieldGroup } from "@/shadcn-ui/ui/field";
import { Input } from "@/shadcn-ui/ui/input";
import { Button } from "@/shadcn-ui/ui/button";

function getPostLoginPath(user: GuestInfo) {
  if (user.current_room_id) {
    return ROUTES.ROOMS_CURRENT;
  }
  return ROUTES.ROOMS;
}

export function LoginForm() {
  const router = useRouter();
  const [isNavigating, startTransition] = useTransition();

  const { control, handleSubmit } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: LOGIN_DEFAULT_VALUES,
  });

  const { mutate, isPending } = useMutation({
    ...guestLoginApiV1AuthGuestLoginPostMutation(),
    onSuccess: (data) => {
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
