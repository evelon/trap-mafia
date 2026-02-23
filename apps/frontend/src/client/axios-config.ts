import { CreateClientConfig } from "./gen/client";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  ...AXIOS_CONFIG,
});

const AXIOS_CONFIG = {};
