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
            registerType: 'autoUpdate',
            manifest: false, // Using local file in public/manifest.webmanifest
            devOptions: {
                enabled: true,
                type: 'module',
            },
            workbox: {
                // Force SW to activate immediately
                skipWaiting: true,
                clientsClaim: true,
                cleanupOutdatedCaches: true,

                // SPA Fallback: Clean URLs
                navigateFallback: '/index.html',
                // Apply fallback to all app routes (exclude API/uploads below)
                navigateFallbackAllowlist: [/^\/(?!api|uploads|manifest\.webmanifest).*/],
                // Do NOT use index.html for API calls or Image uploads
                navigateFallbackDenylist: [/^\/api/, /^\/uploads/, /manifest\.webmanifest$/],

                // Precache these files
                globPatterns: ['**/*.{js,css,html,png,svg,woff2,ico,json}'],

                runtimeCaching: [
                    // 1. Critical Static Assets (Manifest, Icons) - StaleWhileRevalidate
                    // Load fast from cache, check update in background
                    {
                        urlPattern: /(manifest\.webmanifest|icon-.*\.png|favicon\.ico)/i,
                        handler: 'StaleWhileRevalidate',
                        options: {
                            cacheName: 'app-shell-static',
                            expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 30 } // 30 days
                        }
                    },
                    // 2. Google Fonts - CacheFirst (Immutable)
                    {
                        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
                        handler: 'CacheFirst',
                        options: {
                            cacheName: 'google-fonts-cache',
                            expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 }
                        }
                    },
                    // 3. User Uploads (Logos) - CacheFirst (Rarely change, max performance)
                    {
                        urlPattern: /.*\/uploads\/.*\.(png|jpg|jpeg|svg|webp)/i,
                        handler: 'CacheFirst',
                        options: {
                            cacheName: 'user-uploads-cache',
                            expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 * 24 * 365 }
                        }
                    },
                    // 4. API Data (Invoices, Dashboard) - NetworkFirst
                    // Try network. If fails, use Cached response.
                    {
                        urlPattern: /\/api\/.*/i,
                        handler: 'NetworkFirst',
                        options: {
                            cacheName: 'api-data-cache',
                            networkTimeoutSeconds: 5, // Fallback to cache after 5s
                            expiration: {
                                maxEntries: 100,
                                maxAgeSeconds: 60 * 60 * 24 * 7 // 7 days backup
                            },
                            cacheableResponse: {
                                statuses: [0, 200]
                            }
                        }
                    }
                ]
            }
        })
    ],
    server: {
        https: true,
        host: true,
        allowedHosts: ['.ngrok-free.dev'],
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
            // Direct proxies for static files removed to rely on public/ folder
        },
    },
})
