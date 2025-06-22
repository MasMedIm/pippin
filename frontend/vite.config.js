import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      // Proxy API requests during development to the backend container
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
});
