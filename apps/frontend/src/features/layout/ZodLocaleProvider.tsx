"use client";

import z from "zod";
import { ko } from "zod/locales";

/**
 * NOTE: zod locale 설정
 *
 * - `"use client";` client 컴포넌트에서 초기화하지 않으면 설정되지 않음.
 */
z.config(ko());

export function ZodConfigProvider({ children }: { children: React.ReactNode }) {
  return children;
}
