/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Locally, /data/... is passed through to the dataset, like vercel.json does when live
  server: {
    proxy: {
      "/data": {
        target: "https://huggingface.co",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/data/, "/datasets/Anushkajoshii/breathe-check-data/raw/main/public"),
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
});
