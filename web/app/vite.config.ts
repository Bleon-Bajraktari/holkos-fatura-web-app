import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import basicSsl from '@vitejs/plugin-basic-ssl'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
        basicSsl(),
        VitePWA({
            registerType: 'prompt',
            devOptions: {
                enabled: true
            },
            includeAssets: ['icon-192.png', 'icon-512.png', 'apple-touch-icon.png', 'logo.png', 'manifest.webmanifest'],
            workbox: {
                cleanupOutdatedCaches: true,
                navigateFallback: '/index.html',
                globPatterns: ['**/*.{js,css,html,png,svg,woff2,ico,json}'],
                runtimeCaching: [
                    {
                        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
                        handler: 'CacheFirst',
                        options: {
                            cacheName: 'google-fonts-cache',
                            expiration: {
                                maxEntries: 10,
                                maxAgeSeconds: 60 * 60 * 24 * 365 // 365 days
                            },
                            cacheableResponse: {
                                statuses: [0, 200]
                            }
                        }
                    },
                    {
                        urlPattern: /\/api\/dashboard\/stats/i,
                        handler: 'NetworkFirst',
                        options: {
                            cacheName: 'api-stats-cache',
                            expiration: {
                                maxEntries: 5,
                                maxAgeSeconds: 60 * 60 * 24 // 24 hours
                            }
                        }
                    },
                    {
                        urlPattern: /\/api\/.*/i,
                        handler: 'NetworkFirst',
                        options: {
                            cacheName: 'api-data-cache',
                            expiration: {
                                maxEntries: 100,
                                maxAgeSeconds: 60 * 60 * 24 // 24 hours
                            }
                        }
                    },
                    {
                        urlPattern: /.*\/uploads\/.*\.(png|jpg|jpeg|svg|webp|gif)/i,
                        handler: 'CacheFirst',
                        options: {
                            cacheName: 'company-assets-cache',
                            expiration: {
                                maxEntries: 50,
                                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
                            },
                            cacheableResponse: {
                                statuses: [0, 200]
                            }
                        }
                    },
                    {
                        urlPattern: /manifest\.webmanifest/i,
                        handler: 'NetworkFirst',
                        options: {
                            cacheName: 'manifest-cache',
                        }
                    },
                    {
                        urlPattern: /\/logo\.png/i,
                        handler: 'NetworkFirst',
                        options: {
                            cacheName: 'logo-cache',
                        }
                    }
                ]
            }
        })
    ],
    server: {
        https: true,
        host: true,
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path: string) => path.replace(/^\/api/, ''),
            },
            '/uploads': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/logo.png': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/apple-touch-icon.png': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/manifest.webmanifest': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
})
