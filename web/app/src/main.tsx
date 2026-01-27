import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// SW registration handled by vite-plugin-pwa
import { registerSW } from 'virtual:pwa-register'

registerSW({
    onNeedRefresh() {
        if (confirm('Aplikacioni ka një përditësim të ri. A dëshironi ta rifreskoni?')) {
            window.location.reload()
        }
    },
    onOfflineReady() {
        alert('HOLKOS: Sistemi u shkarkua saktë! Tani mund ta përdorni këtë aplikacion edhe pa internet (Offline).')
        console.log('Aplikacioni është gati për përdorim offline!')
    },
})
ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
)
