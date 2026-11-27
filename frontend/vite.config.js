import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Development'da /api so'rovlari Django serveriga yo'naltiriladi.
// Shunda brauzer uchun frontend va backend bitta manzilda turadi va CORS sozlash shart emas.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Docker + Windows: fayl o'zgarishlari faqat polling orqali seziladi (docker-compose.yml → VITE_POLLING)
    watch: process.env.VITE_POLLING ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      // changeOrigin: false — Django brauzer yuborgan Host'ni (localhost:5173) ko'radi.
      // true bo'lsa Docker ichida Host 'web:8000' bo'lib, ALLOWED_HOSTS uni rad etadi (400 Bad Request)
      '/api': { target: process.env.API_PROXY || 'http://127.0.0.1:8000', changeOrigin: false },
      // Arizaga yuklangan rasmlar ham backend'da turadi
      '/media': { target: process.env.API_PROXY || 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
})
