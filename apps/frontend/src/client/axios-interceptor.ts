import { AxiosError, type AxiosRequestConfig } from "axios";
import { client } from "./gen/client.gen";
import { refreshApiV1AuthRefreshPost } from "./gen/sdk.gen";
import { API_PATHS, ROUTES } from "@/shared/routes";

type RetryConfig = AxiosRequestConfig & { _retry?: boolean };

interface PendingRequest {
  resolve: () => void;
  reject: (err: unknown) => void;
}

const AUTH_SKIP_PATHS = [API_PATHS.AUTH_REFRESH, API_PATHS.AUTH_GUEST_LOGIN];

let isInit = false;
let isRefreshing = false;
let pendingQueue: PendingRequest[] = [];

/**
 * setupInterceptor
 *
 * 401 Unauthorized 응답이 발생했을 때 자동으로 토큰을 갱신하고, 실패 시 로그인 페이지로 리다이렉트하는 인터셉터를 설정합니다.
 */
export function setupInterceptors() {
  if (isInit) return;
  isInit = true;

  client.instance.interceptors.response.use(
    (response) => response,
    handleResponseError,
  );
}

/**
 * handleResponseError
 *
 * 401 Unauthorized 응답이 발생했을 때 토큰 갱신을 시도하고, 갱신 중에는 추가 요청을 큐에 저장합니다.
 * 갱신이 성공하면 큐에 저장된 요청을 재시도하고, 실패하면 로그인 페이지로 리다이렉트합니다.
 */
async function handleResponseError(error: AxiosError) {
  /**
   * "use client" 모듈이라도 SSR 시 서버에서 실행될 수 있다.
   * 서버에서는 refresh나 window.location 리다이렉트를 수행할 수 없으므로
   * 에러를 그대로 전파한다.
   */
  if (typeof window === "undefined") {
    return Promise.reject(error);
  }

  const originalRequest = error.config as RetryConfig | undefined;

  if (
    !originalRequest ||
    !isUnauthorized(error) ||
    isAuthRequest(originalRequest)
  ) {
    // 재시도 대상이 아니면 그대로 실패 처리
    return Promise.reject(error);
  }

  if (originalRequest._retry) {
    // 동일 요청에 대해 1회 이상 refresh 시도는 하지 않음
    return Promise.reject(error);
  }
  originalRequest._retry = true;

  if (isRefreshing) {
    // 다른 요청이 refresh 중이면 큐에 대기
    return enqueueRequest(originalRequest);
  }

  // refresh 실행 시작
  isRefreshing = true;

  try {
    // refresh 성공 시 대기 큐 처리 후 원래 요청 재시도
    await refreshToken();
    processQueue();
    return client.instance(originalRequest);
  } catch {
    /**
     * refresh 실패 시 모든 대기 요청 실패 처리 후 로그인으로 이동.
     * 큐에 원본 401 에러를 전달한다. 대기 중인 요청들도 동일하게 401이 원인이므로
     * 의미적으로 동일하며, refresh 에러를 전달하면 caller가 예상하는 에러 형태와 달라질 수 있다.
     */
    processQueue(error);
    redirectToLogin();
    return Promise.reject(error);
  } finally {
    // refresh 플래그 초기화
    isRefreshing = false;
  }
}

/**
 * 헬퍼 함수
 */

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

function isUnauthorized(error: AxiosError) {
  return error.response?.status === 401;
}

function isAuthRequest(config?: AxiosRequestConfig) {
  return AUTH_SKIP_PATHS.some((path) => config?.url?.includes(path));
}

function redirectToLogin() {
  window.location.href = `${ROUTES.LOGIN}?expired`;
}

function enqueueRequest(config: RetryConfig) {
  return new Promise<void>((resolve, reject) => {
    pendingQueue.push({ resolve, reject });
  }).then(() => client.instance(config));
}

async function refreshToken() {
  await refreshApiV1AuthRefreshPost({ throwOnError: true });
}
