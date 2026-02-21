"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function LoginForm() {
  const [username, setUsername] = useState("");

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-2xl">로그인</CardTitle>
      </CardHeader>
      <CardContent>
        <Input
          placeholder="닉네임을 입력하세요"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </CardContent>
      <CardFooter>
        <Button className="w-full" disabled={!username.trim()}>
          로그인
        </Button>
      </CardFooter>
    </Card>
  );
}
