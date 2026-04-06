import { NextRequest, NextResponse } from "next/server";
import { ROUTES } from "@/shared/routes";

const UNAUTHED_ONLY_PATHS = [ROUTES.LOGIN];
const PUBLIC_PATHS: string[] = [];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isUnauthedOnly = isUnauthedOnlyPath(pathname);
  const isPublic = isPublicPath(pathname);
  const isProtected = !isUnauthedOnly && !isPublic;

  const hasToken = Boolean(request.cookies.get("access_token"));
  const hasExpiredParam = request.nextUrl.searchParams.has("expired");

  // 로그인 상태에서 비로그인 전용 경로 접근 시 /rooms로 리다이렉트
  // 단, 세션 만료로 인한 강제 이동(?expired)은 리다이렉트하지 않는다.
  if (isUnauthedOnly && hasToken && !hasExpiredParam) {
    return NextResponse.redirect(new URL(ROUTES.ROOMS, request.url));
  }

  // 비로그인 상태에서 보호 경로 접근 시 /login으로 리다이렉트
  if (isProtected && !hasToken) {
    return NextResponse.redirect(new URL(ROUTES.LOGIN, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};

/**
 * 헬퍼 함수
 */

function isUnauthedOnlyPath(pathname: string) {
  return UNAUTHED_ONLY_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/"),
  );
}

function isPublicPath(pathname: string) {
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/"),
  );
}
