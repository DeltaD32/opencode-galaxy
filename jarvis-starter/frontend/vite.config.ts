import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The galaxy talks to the gateway daemon (Module C) at localhost:8132.
export default defineConfig({
  plugins: [react()],
  server: { port: 5273 },
});
