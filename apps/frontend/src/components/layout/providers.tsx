import ReactQueryProvider from "./ReactQueryProvider";
import { ZodConfigProvider } from "./ZodLocaleProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ReactQueryProvider>
      <ZodConfigProvider>{children}</ZodConfigProvider>
    </ReactQueryProvider>
  );
}
