"use client";

import { setupInterceptors } from "@/client/axios-interceptor";

setupInterceptors();

export function AxiosSetter({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
