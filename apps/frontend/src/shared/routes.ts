export const ROUTES = {
  LOGIN: "/login",
  ROOMS: "/rooms",
  ROOMS_CURRENT: "/rooms/current",
  CASE: (caseId: string) => `/case/${caseId}`,
} as const;

export const API_PATHS = {
  AUTH_REFRESH: "/auth/refresh",
  AUTH_GUEST_LOGIN: "/auth/guest-login",
} as const;
