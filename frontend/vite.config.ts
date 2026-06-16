import { reactRouter } from '@react-router/dev/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  // Dev server port. Override per-run with PORT, e.g. `PORT=5173 npm run dev`.
  server: { port: Number(process.env.PORT) || 5001 },
});
