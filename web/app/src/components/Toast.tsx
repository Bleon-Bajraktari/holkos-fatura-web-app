import { useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { ToastContext, ToastType, Toast } from '../hooks/useToast'

const ICONS: Record<ToastType, React.ReactNode> = {
    success: <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />,
    error: <XCircle size={18} className="text-rose-500 shrink-0" />,
    warning: <AlertTriangle size={18} className="text-amber-500 shrink-0" />,
    info: <Info size={18} className="text-blue-500 shrink-0" />,
}

const BORDER: Record<ToastType, string> = {
    success: 'border-emerald-200 dark:border-emerald-800',
    error: 'border-rose-200 dark:border-rose-800',
    warning: 'border-amber-200 dark:border-amber-800',
    info: 'border-blue-200 dark:border-blue-800',
}

let idCounter = 0

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
    const [toasts, setToasts] = useState<Toast[]>([])

    const dismiss = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    const add = useCallback((type: ToastType, message: string) => {
        const id = String(++idCounter)
        setToasts(prev => [...prev.slice(-4), { id, type, message }])
        setTimeout(() => dismiss(id), 4000)
    }, [dismiss])

    const ctx = {
        success: (m: string) => add('success', m),
        error: (m: string) => add('error', m),
        info: (m: string) => add('info', m),
        warning: (m: string) => add('warning', m),
    }

    return (
        <ToastContext.Provider value={ctx}>
            {children}
            <div className="fixed z-[100] flex flex-col gap-2 bottom-[calc(var(--nav-height,60px)+12px)] left-3 right-3 lg:left-auto lg:right-4 lg:w-80 pointer-events-none">
                <AnimatePresence>
                    {toasts.map(t => (
                        <motion.div
                            key={t.id}
                            initial={{ opacity: 0, y: 16, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -8, scale: 0.95 }}
                            transition={{ duration: 0.2 }}
                            className={`pointer-events-auto flex items-start gap-3 bg-card border ${BORDER[t.type]} rounded-2xl px-4 py-3 shadow-lg`}
                        >
                            {ICONS[t.type]}
                            <span className="flex-1 text-sm font-semibold text-foreground leading-snug">{t.message}</span>
                            <button
                                onClick={() => dismiss(t.id)}
                                className="p-0.5 text-muted-foreground hover:text-foreground transition-colors shrink-0 mt-px"
                            >
                                <X size={14} />
                            </button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    )
}

export default ToastProvider
