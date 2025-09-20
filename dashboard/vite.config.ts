import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'path';

export default defineConfig(({ mode }) => {
    const isDev = mode === 'development';
    
    return {
        plugins: [
            tsconfigPaths(),
            react(), // Fixed from SWC to regular React plugin
            ...(mode === 'analyze' ? [
                visualizer({
                    filename: 'dist/bundle-analysis.html',
                    open: false,
                    gzipSize: true,
                    brotliSize: true
                })
            ] : [])
        ],
        server: {
            host: '0.0.0.0',
            port: 5000,
            strictPort: true,
            allowedHosts: true
        },
        define: {
            __DEV__: isDev,
            'process.env.NODE_ENV': JSON.stringify(mode)
        },
        esbuild: {
            legalComments: 'none',
            keepNames: isDev, // Only keep names in development
            ...(!isDev && {
                // Production optimizations
                drop: ['console', 'debugger'], // Remove console logs and debugger statements
                minifyIdentifiers: true,
                minifySyntax: true,
                minifyWhitespace: true
            }),
            ...(isDev && {
                minifyIdentifiers: false,
                minifySyntax: false,
                minifyWhitespace: false
            })
        },
        build: {
            assetsDir: 'static',
            outDir: 'dist',
            sourcemap: isDev, // Only generate sourcemaps in development
            minify: isDev ? false : 'esbuild', // Enable minification in production
            chunkSizeWarningLimit: 600,
            target: 'esnext',
            rollupOptions: {
                output: {
                    manualChunks: (id: string) => {
                        // Core React dependencies - keep minimal and clean
                        if (id.includes('react-dom') || id.includes('react/') || id.includes('react\\')) {
                            return 'react-core';
                        }
                        
                        // Monaco Editor - lazy loaded, separate chunk
                        if (id.includes('@monaco-editor') || id.includes('monaco-editor')) {
                            return 'monaco';
                        }
                        
                        // Recharts - lazy loaded, separate chunk
                        if (id.includes('recharts')) {
                            return 'recharts';
                        }
                        
                        // DND Kit - lazy loaded, separate chunk  
                        if (id.includes('@dnd-kit/')) {
                            return 'dnd-kit';
                        }
                        
                        // TanStack - split by functionality
                        if (id.includes('@tanstack/react-router')) {
                            return 'router';
                        }
                        if (id.includes('@tanstack/react-query')) {
                            return 'query';
                        }
                        if (id.includes('@tanstack/react-table')) {
                            return 'table';
                        }
                        
                        // Forms and validation - frequently used together
                        if (id.includes('react-hook-form') || id.includes('@hookform/') || id.includes('zod')) {
                            return 'forms';
                        }
                        
                        // UI and styling utilities - split for better caching
                        if (id.includes('lucide-react')) {
                            return 'icons';
                        }
                        if (id.includes('class-variance-authority') || id.includes('clsx') || id.includes('tailwind-merge')) {
                            return 'styling-utils';
                        }
                        if (id.includes('next-themes')) {
                            return 'theme';
                        }
                        
                        // Date and utility libraries
                        if (id.includes('date-fns')) {
                            return 'date-utils';
                        }
                        
                        // Network and data libraries
                        if (id.includes('ofetch') || id.includes('yaml')) {
                            return 'network';
                        }
                        
                        // Development and testing tools (only in dev builds)
                        if (isDev && (id.includes('@testing-library') || id.includes('vitest') || id.includes('@hookform/devtools'))) {
                            return 'dev-tools';
                        }
                        
                        // Command palette and search
                        if (id.includes('cmdk') || id.includes('use-debounce')) {
                            return 'search';
                        }
                        
                        // State management
                        if (id.includes('zustand') || id.includes('@uidotdev/usehooks') || id.includes('use-sync-external-store')) {
                            return 'state';
                        }
                        
                        // Layout and panels
                        if (id.includes('react-resizable-panels') || id.includes('react-day-picker')) {
                            return 'layout';
                        }
                        
                        // React ecosystem - group all React-dependent libraries together
                        // This includes Radix UI, i18n, and small React components
                        if (id.includes('@radix-ui/') || 
                            id.includes('i18next') || 
                            id.includes('react-i18next') ||
                            id.includes('react-copy-to-clipboard') || 
                            id.includes('react-qr-code') || 
                            id.includes('sonner') || 
                            id.includes('vaul')) {
                            return 'react-ecosystem';
                        }
                        
                        // Large vendor dependencies that should be separate
                        if (id.includes('node_modules')) {
                            // Keep remaining large libraries in separate chunks
                            const packageName = id.split('node_modules/')[1]?.split('/')[0];
                            if (packageName && ['@codemirror'].includes(packageName)) {
                                return `vendor-${packageName.replace('@', '')}`;
                            }
                        }
                    }
                }
            }
        },
        resolve: {
            dedupe: ['react', 'react-dom'], // Critical fix for React conflicts
            alias: [
                {
                    find: '@wildosvpn',
                    replacement: path.resolve(__dirname, './src/'),
                },
            ],
        },
    }
})