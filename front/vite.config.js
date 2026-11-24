import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/popular-banco": "http://127.0.0.1:5000",
      "/public": "http://127.0.0.1:5000",
    },
  },
});
