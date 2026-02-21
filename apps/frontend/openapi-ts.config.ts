import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8000/openapi.json",
  output: {
    path: "./src/client",
    postProcess: ["prettier"],
  },
  plugins: [
    // "@hey-api/schemas",
    // {
    //   dates: true,
    //   name: "@hey-api/transformers",
    // },
    // {
    //   name: "@hey-api/sdk",
    //   transformer: true,
    // },
    "@hey-api/typescript",
    "@hey-api/client-axios",
    "zod",
    "@tanstack/react-query",
  ],
});
