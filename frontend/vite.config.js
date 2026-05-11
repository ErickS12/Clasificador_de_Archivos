import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // <-- Añade esto

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // <-- Añade esto
  ],
})