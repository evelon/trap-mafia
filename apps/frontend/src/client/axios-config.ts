import { ClientOptions, Config, CreateClientConfig } from "./gen/client";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  ...AXIOS_CONFIG,
});

const AXIOS_CONFIG: Config<ClientOptions> = {
  /*
   * NOTE
   * - https://localhost:443 (443이 기본 포트라 포트 명시 안해도 됨)
   * - 프론트 접속시 https로 접속해야 함
   *
   * TODO
   * - 추후 prod 환경은 배포 경로로 분기
   */
  baseURL: "https://localhost",

  withCredentials: true,
};
