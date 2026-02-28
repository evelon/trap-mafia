import { AxiosSetter } from "./AxiosSetter";
import ReactQueryProvider from "./ReactQueryProvider";
import { ZodConfigSetter } from "./ZodConfigSetter";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AxiosSetter>
      <ReactQueryProvider>
        <ZodConfigSetter>{children}</ZodConfigSetter>
      </ReactQueryProvider>
    </AxiosSetter>
  );
}
