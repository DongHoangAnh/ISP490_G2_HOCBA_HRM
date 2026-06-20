import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev:   npm run dev  → http://localhost:5173, proxy API về Odoo Docker.
//        Odoo bind cả IPv6; dùng [::1] để chắc chắn vào Docker chứ không phải
//        Odoo native Windows (xem docs/DEV_LOCAL.md).
// Build: npm run build → custom-addons/hocba_hrm/static/spa/, Odoo serve
//        qua route /hocba-hrm (controllers/main.py).
export default defineConfig({
  plugins: [react()],
  base: '/hocba_hrm/static/spa/',
  server: {
    proxy: {
      '/hocba-hrm/api': { target: 'http://[::1]:8069', changeOrigin: false },
      '/hocba_employees/static': { target: 'http://[::1]:8069', changeOrigin: false },
      '/web': { target: 'http://[::1]:8069', changeOrigin: false },
      '/odoo': { target: 'http://[::1]:8069', changeOrigin: false },
    },
  },
  build: {
    outDir: '../custom-addons/hocba_hrm/static/spa',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/index.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
  },
});
