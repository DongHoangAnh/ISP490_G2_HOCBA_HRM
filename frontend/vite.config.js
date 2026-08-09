import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev:   npm run dev  → http://localhost:5173, proxy API về Odoo Docker.
//        Stack Neon (docker-compose.onl.yml) publish cổng 8070 → proxy vào
//        127.0.0.1:8070, tránh đụng Odoo native Windows đang giữ 8069.
// Build: npm run build → custom-addons/hocba_hrm/static/spa/, Odoo serve
//        qua route /hocba-hrm (controllers/main.py).
export default defineConfig({
  plugins: [react()],
  base: '/hocba_hrm/static/spa/',
  server: {
    proxy: {
      '/hocba-hrm/api': { target: 'http://127.0.0.1:8070', changeOrigin: false },
      '/hocba-hrm': { target: 'http://127.0.0.1:8070', changeOrigin: false },
      '/hocba_employees/static': { target: 'http://127.0.0.1:8070', changeOrigin: false },
      '/web': { target: 'http://127.0.0.1:8070', changeOrigin: false },
      '/odoo': { target: 'http://127.0.0.1:8070', changeOrigin: false },
      '/jobs': { target: 'http://127.0.0.1:8070', changeOrigin: false },
      '/website': { target: 'http://127.0.0.1:8070', changeOrigin: false },
    },
  },
  build: {
    outDir: '../custom-addons/hocba_hrm/static/spa',
    emptyOutDir: true,
    // Tên file CỐ ĐỊNH (không content-hash) để mỗi lần build không sinh bundle
    // mới → tránh conflict git ở static/spa mỗi lần push. Chống cache trình
    // duyệt được xử lý ở controller: thêm ?v=<hash nội dung> vào URL asset khi
    // serve index.html (xem controllers/main.py::hrm_dashboard).
    rollupOptions: {
      output: {
        entryFileNames: 'assets/index.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
  },
});
