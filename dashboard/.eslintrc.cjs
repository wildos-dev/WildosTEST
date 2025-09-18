module.exports = {
    root: true,
    env: { browser: true, es2020: true },
    extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended', 'plugin:react-hooks/recommended'],
    ignorePatterns: ['dist', '.eslintrc.cjs'],
    parser: '@typescript-eslint/parser',
    plugins: ['react-refresh'],
    rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        'react-refresh/only-export-components': 'off',
        // Prevent direct imports of HTTP clients to enforce unified architecture
        'no-restricted-imports': ['error', {
            paths: [
                {
                    name: 'ofetch',
                    message: 'Direct import of ofetch is not allowed. Use apiClient or externalApi from "@/common/utils/http" instead for unified error handling and auth injection.'
                },
                {
                    name: 'node-fetch',
                    message: 'Direct import of node-fetch is not allowed. Use apiClient or externalApi from "@/common/utils/http" instead.'
                },
                {
                    name: 'cross-fetch',
                    message: 'Direct import of cross-fetch is not allowed. Use apiClient or externalApi from "@/common/utils/http" instead.'
                },
                {
                    name: 'react-use-websocket',
                    message: 'Direct import of react-use-websocket is not allowed. Use useEnhancedWebSocket from "@/common/hooks/use-enhanced-websocket" instead for consistent reconnection and auth token injection.'
                }
            ],
            patterns: [
                {
                    group: ['ofetch/*', 'node-fetch/*', 'cross-fetch/*', 'react-use-websocket/*'],
                    message: 'Direct imports of HTTP/WebSocket libraries are not allowed. Use the unified clients/hooks from "@/common" instead.'
                }
            ]
        }],
    },
    overrides: [
        {
            // Allow http.ts wrapper to import ofetch directly since it IS the unified client
            files: ['src/common/utils/http.ts'],
            rules: {
                'no-restricted-imports': 'off'
            }
        }
    ]
};