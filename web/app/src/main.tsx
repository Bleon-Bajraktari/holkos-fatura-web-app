import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// SW registration handled by vite-plugin-pwa
import { registerSW } from 'virtual:pwa-register'

if (import.meta.env.PROD) {
    const updateSW = registerSW({
        immediate: true,
        onNeedRefresh() {
            updateSW(true)
        },
        onOfflineReady() {
            console.log('Aplikacioni është gati për përdorim offline!')
        },
    })
}
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: any, errorInfo: any) {
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
                    <h1 className="text-xl font-bold text-red-600 mb-2">Ndodhi një gabim!</h1>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                        Rifresko Faqen
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ErrorBoundary>
            <App />
        </ErrorBoundary>
    </React.StrictMode>,
)
