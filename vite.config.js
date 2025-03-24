import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import * as path from 'path';

export default defineConfig({
  plugins: [vue()],
  base: './',
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  build: {
    // 输出目录设置为 ../docs
    outDir: path.resolve(__dirname, 'docs'),
    // 静态资源直接输出到 docs 文件夹下
    assetsDir: ''
  },
  server: {
    port: 8080,
    open: true
  }
})
