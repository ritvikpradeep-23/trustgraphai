import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: { "/api": { target: process.env.TRUSTGRAPH_API_URL ?? "http://127.0.0.1:8000", changeOrigin: true } },
  },
  resolve: {
    alias: {
      "lucide-react-upstream": path.resolve(__dirname, "node_modules/lucide-react"),
      "lucide-react": path.resolve(__dirname, "src/lib/lucide-react.tsx"),
      "@": path.resolve(__dirname, "src"),
    },
  },
});
