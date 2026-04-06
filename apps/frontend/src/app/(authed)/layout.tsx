import { meApiV1AuthMeGetQueryKey } from "@/client/gen/@tanstack/react-query.gen";
import { meApiV1AuthMeGet } from "@/client/gen/sdk.gen";
import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { headers } from "next/headers";

interface Props {
  children: React.ReactNode;
}

export default async function AuthedLayout({ children }: Props) {
  const queryClient = new QueryClient();
  await prefetchMe(queryClient);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
}

async function prefetchMe(queryClient: QueryClient) {
  // NOTE: ref - https://nextjs.org/docs/app/api-reference/functions/headers
  const headersList = await headers();
  const cookieHeader = headersList.get("cookie");

  try {
    const { data } = await meApiV1AuthMeGet({
      headers: { Cookie: cookieHeader },
      throwOnError: true,
    });
    queryClient.setQueryData(meApiV1AuthMeGetQueryKey(), data);
  } catch {
    /**
     * 401 등은 비로그인으로 간주하고 SSR을 계속 진행한다.
     *
     * - throwOnError: true로 에러는 throw되고 여기서 무시됨. 따라서 실패 시 캐시에 아무것도 넣지 않는다.
     * - 만약 throwOnError: false로 try/catch 없이 작성하면, 요청 실패시 undefined가 "성공"으로 캐시되어
     * 클라이언트 재요청이 막힐 수 있다.
     */
  }
}
