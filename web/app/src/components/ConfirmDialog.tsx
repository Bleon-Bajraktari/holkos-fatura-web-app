import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'

interface ConfirmDialogProps {
    isOpen: boolean
    title: string
    message: string
    confirmLabel?: string
    cancelLabel?: string
    onConfirm: () => void
    onCancel: () => void
    danger?: boolean
}

const ConfirmDialog = ({
    isOpen,
    title,
    message,
    confirmLabel = 'Konfirmo',
    cancelLabel = 'Anulo',
    onConfirm,
    onCancel,
    danger = true,
}: ConfirmDialogProps) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={onCancel}
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 8 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 8 }}
                        transition={{ duration: 0.2 }}
                        className="relative w-full max-w-sm bg-card rounded-2xl border border-border shadow-2xl p-6 space-y-4"
                    >
                        <div className="flex items-start gap-3">
                            {danger && (
                                <div className="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950/40 flex items-center justify-center shrink-0">
                                    <AlertTriangle size={20} className="text-rose-500" />
                                </div>
                            )}
                            <div>
                                <h3 className="font-black text-foreground text-base">{title}</h3>
                                <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{message}</p>
                            </div>
                        </div>

                        <div className="flex gap-2 pt-1">
                            <button
                                onClick={onCancel}
                                className="btn-secondary flex-1 py-2.5 text-sm"
                            >
                                {cancelLabel}
                            </button>
                            <button
                                onClick={onConfirm}
                                className={`flex-1 py-2.5 text-sm rounded-xl font-bold transition-all duration-150 flex items-center justify-center gap-2 ${
                                    danger
                                        ? 'btn-danger'
                                        : 'btn-primary'
                                }`}
                            >
                                {confirmLabel}
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}

export default ConfirmDialog
