import { createContext, useContext } from 'react'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
    id: string
    type: ToastType
    message: string
}

export interface ToastContextValue {
    success: (message: string) => void
    error: (message: string) => void
    info: (message: string) => void
    warning: (message: string) => void
}

export const ToastContext = createContext<ToastContextValue>({
    success: () => {},
    error: () => {},
    info: () => {},
    warning: () => {},
})

export const useToast = () => useContext(ToastContext)
