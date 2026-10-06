import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "lucide-react-upstream": path.resolve(__dirname, "node_modules/lucide-react"),
      "lucide-react": path.resolve(__dirname, "src/lib/lucide-react.tsx"),
      "@": path.resolve(__dirname, "src"),
    },
  },
});
