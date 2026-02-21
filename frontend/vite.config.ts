import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          graph: ['react-force-graph-2d'],
          auth: ['@clerk/clerk-react'],
          markdown: ['react-markdown', 'remark-gfm', 'remark-math', 'rehype-katex'],
          icons: ['lucide-react']
        }
      }
    }
  }
})
