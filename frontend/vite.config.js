import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from the root directory (../)
  // process.cwd() is likely the 'frontend' dir when running 'vite', so '..' gets us to root.
  const env = loadEnv(mode, path.resolve(process.cwd(), '..'), '')

  const backendPort = env.BACKEND_PORT || 5000
  const frontendPort = parseInt(env.FRONTEND_PORT) || 5173

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
    },
    define: {
      __BACKEND_PORT__: JSON.stringify(backendPort),
    }
  }
})
