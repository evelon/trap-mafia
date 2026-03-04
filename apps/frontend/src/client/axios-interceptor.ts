import { AxiosError } from "axios";
import { client } from "./gen/client.gen";
import { refreshApiV1AuthRefreshPost } from "./gen/sdk.gen";

// 토큰 리프레시 중복 방지를 위한 상태
let isRefreshing = false;

// 리프레시 대기 중인 요청들의 콜백 큐
let pendingQueue: Array<{
  resolve: () => void;
  reject: (err: unknown) => void;
}> = [];

/** 대기 중인 요청들을 일괄 처리 (리프레시 성공 시 resolve, 실패 시 reject) */
function processQueue(error: unknown = null) {
  for (const { resolve, reject } of pendingQueue) {
    if (error) {
      reject(error);
    } else {
      resolve();
    }
  }
  pendingQueue = [];
}

/** 토큰 리프레시를 시도하지 않을 인증 관련 경로 */
const AUTH_SKIP_PATHS = ["/auth/refresh", "/auth/guest-login"];

/** 401 응답 시 토큰 리프레시 후 원래 요청을 재시도 */
async function handleUnauthorized(error: AxiosError) {
  const originalRequest = error.config;

  const isUnauthorized = error.response?.status === 401;
  const isAuthRequest = AUTH_SKIP_PATHS.some((path) =>
    originalRequest?.url?.includes(path),
  );

  // 요청 정보가 없거나, 401이 아니거나, 인증 요청 자체가 실패한 경우 → retry 불필요
  if (!originalRequest || !isUnauthorized || isAuthRequest) {
    return Promise.reject(error);
  }

  // 이미 리프레시 진행 중이면 큐에 대기 후, 완료되면 원래 요청 재시도
  if (isRefreshing) {
    return new Promise<void>((resolve, reject) => {
      pendingQueue.push({ resolve, reject });
    }).then(() => client.instance(originalRequest));
  }

  isRefreshing = true;

  try {
    // 토큰 리프레시 후 대기 큐 처리 및 원래 요청 재시도
    await refreshApiV1AuthRefreshPost();
    processQueue();
    return client.instance(originalRequest);
  } catch (refreshError) {
    processQueue(refreshError);
    // 리프레시도 실패 → 세션 만료로 간주하고 로그인 페이지로 이동
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    return Promise.reject(refreshError);
  } finally {
    isRefreshing = false;
  }
}

let isInit = false;

export function setupInterceptors() {
  if (isInit) return;
  isInit = true;

  client.instance.interceptors.response.use(
    (response) => response,
    handleUnauthorized,
  );
}
