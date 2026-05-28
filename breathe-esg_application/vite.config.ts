import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],

    // ── Dev server proxy ────────────────────────────────────────────────────
    // In production the frontend is a static build served by Railway.
    // The browser calls VITE_API_URL directly — no proxy needed.
    // In local dev, proxy /api → Django to avoid CORS entirely.
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },

    // ── Build ───────────────────────────────────────────────────────────────
    build: {
      outDir: 'dist',
      sourcemap: false,         // disable in prod to reduce bundle size
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          // Split vendor chunks for better caching
          manualChunks: {
            react:  ['react', 'react-dom'],
            router: ['react-router-dom'],
            query:  ['@tanstack/react-query'],
            axios:  ['axios'],
          },
        },
      },
    },
  }
})