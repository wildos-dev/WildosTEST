/// <reference types="vitest" />
import { defineConfig } from 'vite'
// @ts-ignore
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/config/vitest.setup.ts'],
    css: true,
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './test/coverage',
      include: [
        'dashboard/src/**/*.{ts,tsx}',
        '!dashboard/src/**/*.d.ts',
        '!dashboard/src/**/*.test.{ts,tsx}',
        '!dashboard/src/**/*.spec.{ts,tsx}',
        '!dashboard/src/main.tsx',
        '!dashboard/src/vite-env.d.ts'
      ],
      exclude: [
        'node_modules/',
        'test/',
        'dist/',
        '**/*.d.ts'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    testTimeout: 10000,
    hookTimeout: 10000
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../../dashboard/src'),
      '@assets': path.resolve(__dirname, '../../dashboard/src/assets'),
      '@lib': path.resolve(__dirname, '../../dashboard/src/libs'),
      '@components': path.resolve(__dirname, '../../dashboard/src/common/components'),
      '@features': path.resolve(__dirname, '../../dashboard/src/features'),
      '@modules': path.resolve(__dirname, '../../dashboard/src/modules'),
      '@hooks': path.resolve(__dirname, '../../dashboard/src/common/hooks'),
      '@utils': path.resolve(__dirname, '../../dashboard/src/common/utils'),
      '@types': path.resolve(__dirname, '../../dashboard/src/common/types')
    }
  }
})