"use client";

import { Button } from "@/shadcn-ui/ui/button";
import { Card, CardContent, CardFooter } from "@/shadcn-ui/ui/card";

interface Props {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function AuthedError({ reset }: Props) {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 text-center">
          <p className="text-destructive">문제가 발생했습니다.</p>
        </CardContent>
        <CardFooter className="justify-center">
          <Button onClick={reset}>다시 시도</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
