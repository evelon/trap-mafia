import { zGuestLoginRequest } from "@/client/gen/zod.gen";
import { refineField } from "@/lib/zod";
import z from "zod";

export const loginSchema = refineField(zGuestLoginRequest, {
  field: "username",
  check: (val) => val.trim().length > 0,
  message: "공백만 입력할 수 없습니다",
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const LOGIN_DEFAULT_VALUES: LoginFormValues = { username: "" };
