import { ClientOptions, Config, CreateClientConfig } from "./gen/client";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  ...AXIOS_CONFIG,
});

const AXIOS_CONFIG: Config<ClientOptions> = {
  // baseURL: "http://localhost:8000",
  baseURL: "https://localhost:443", // TODO: 로컬 외 셋팅
  withCredentials: true,
};
