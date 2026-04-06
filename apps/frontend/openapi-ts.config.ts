import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8000/openapi.json",
  output: {
    path: "./src/client/gen",
    postProcess: ["prettier"],
    entryFile: false,
  },
  plugins: [
    {
      name: "@hey-api/sdk",
    },
    "@hey-api/typescript",
    {
      name: "@hey-api/client-axios",
      runtimeConfigPath: "../axios-config",
    },
    "zod",
    {
      name: "@tanstack/react-query",
      // includeInEntry: true,
    },
  ],
});
