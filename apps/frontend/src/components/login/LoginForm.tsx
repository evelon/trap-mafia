"use client";

import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
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
import { guestLoginApiV1AuthGuestLoginPostMutation } from "@/client/@tanstack/react-query.gen";
import { zGuestLoginRequest } from "@/client/zod.gen";
import { refineField } from "@/lib/zod";
import { toast } from "sonner";

const schema = refineField(zGuestLoginRequest, {
  field: "username",
  check: (val) => val.trim().length > 0,
  message: "공백만 입력할 수 없습니다",
});

type FormValues = z.infer<typeof schema>;

export function LoginForm() {
  const router = useRouter();

  const { control, handleSubmit } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "" },
  });

  const { mutate, isPending } = useMutation({
    ...guestLoginApiV1AuthGuestLoginPostMutation(),
    onSuccess: (data) => {
      if (data.data?.in_case) {
        router.push(`/case/${data.data.current_case_id}`);
      } else {
        router.push("/rooms");
      }
    },
    onError: () => {
      toast.error("로그인에 실패했습니다. 다시 시도해주세요.");
    },
  });

  const onSubmit = ({ username }: FormValues) => {
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
                    disabled={isPending}
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
          disabled={isPending}
        >
          {isPending ? "로그인 중..." : "로그인"}
        </Button>
      </CardFooter>
    </Card>
  );
}
