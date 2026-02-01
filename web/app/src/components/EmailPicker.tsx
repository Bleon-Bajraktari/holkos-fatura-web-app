import { useEffect, useMemo, useState } from 'react'
import { Loader2, Mail, Trash2, X } from 'lucide-react'

const STORAGE_KEY = 'saved_emails'

const loadEmails = (): string[] => {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) return []
        const parsed = JSON.parse(raw)
        return Array.isArray(parsed) ? parsed : []
    } catch {
        return []
    }
}

const saveEmails = (emails: string[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(emails))
}

type Props = {
    isOpen: boolean
    title?: string
    initialEmail?: string
    allowClientEmail?: boolean
    onClose: () => void
    onConfirm: (email: string) => void | Promise<void>
    onConfirmClientEmail?: () => void | Promise<void>
}

const EmailPicker = ({
    isOpen,
    title = 'Zgjidh Email',
    initialEmail = '',
    allowClientEmail = false,
    onClose,
    onConfirm,
    onConfirmClientEmail
}: Props) => {
    const [emails, setEmails] = useState<string[]>([])
    const [email, setEmail] = useState('')
    const [remember, setRemember] = useState(true)
    const [sending, setSending] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)

    useEffect(() => {
        if (!isOpen) return
        const stored = loadEmails()
        setEmails(stored)
        setEmail(initialEmail || stored[0] || '')
        setError(null)
        setSuccess(false)
    }, [isOpen, initialEmail])

    const isValid = useMemo(() => {
        if (!email) return false
        return /.+@.+\..+/.test(email)
    }, [email])

    const handleSaveEmail = (value: string) => {
        const trimmed = value.trim()
        if (!trimmed) return
        const next = Array.from(new Set([trimmed, ...emails]))
        setEmails(next)
        saveEmails(next)
    }

    const handleDelete = (value: string) => {
        const next = emails.filter(e => e !== value)
        setEmails(next)
        saveEmails(next)
        if (email === value) {
            setEmail(next[0] || '')
        }
    }

    const handleConfirm = async () => {
        if (!isValid || sending) return
        setSending(true)
        setError(null)
        try {
            if (remember) handleSaveEmail(email)
            await onConfirm(email.trim())
            setSuccess(true)
            setTimeout(() => onClose(), 800)
        } catch (e: any) {
            const msg = e?.response?.data?.detail ?? e?.message ?? 'Gabim gjatë dërgimit të email-it.'
            setError(String(msg))
        } finally {
            setSending(false)
        }
    }

    const handleConfirmClientEmail = async () => {
        if (!onConfirmClientEmail || sending) return
        setSending(true)
        setError(null)
        try {
            await onConfirmClientEmail()
            setSuccess(true)
            setTimeout(() => onClose(), 800)
        } catch (e: any) {
            const msg = e?.response?.data?.detail ?? e?.message ?? 'Gabim gjatë dërgimit të email-it.'
            setError(String(msg))
        } finally {
            setSending(false)
        }
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100">
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
                    <div className="flex items-center gap-2 text-slate-800 font-bold">
                        <Mail size={18} />
                        <span>{title}</span>
                    </div>
                    <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg">
                        <X size={18} />
                    </button>
                </div>

                <div className="p-5 space-y-4">
                    <div>
                        <label className="text-xs font-bold text-slate-500">Emaili</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="shembull@email.com"
                            disabled={sending}
                            className="mt-2 w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-semibold focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all disabled:opacity-60"
                        />
                    </div>

                    {emails.length > 0 && (
                        <div>
                            <p className="text-xs font-bold text-slate-500 mb-2">Email-at e ruajtur</p>
                            <div className="space-y-2 max-h-40 overflow-auto">
                                {emails.map(e => (
                                    <div key={e} className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
                                        <button
                                            onClick={() => setEmail(e)}
                                            className="text-sm font-semibold text-slate-700 text-left"
                                        >
                                            {e}
                                        </button>
                                        <button onClick={() => handleDelete(e)} className="p-1 text-slate-400 hover:text-red-500">
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <label className="flex items-center gap-2 text-sm text-slate-600">
                        <input
                            type="checkbox"
                            checked={remember}
                            onChange={(e) => setRemember(e.target.checked)}
                            disabled={sending}
                        />
                        Ruaj këtë email
                    </label>

                    {error && (
                        <div className="px-3 py-2.5 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 font-medium">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="px-3 py-2.5 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 font-medium">
                            Email u dërgua me sukses!
                        </div>
                    )}
                </div>

                <div className="flex flex-col sm:flex-row gap-2 px-5 pb-5">
                    
                    <button
                        onClick={handleConfirm}
                        disabled={!isValid || sending}
                        className="w-full sm:w-auto px-4 py-2.5 text-sm font-bold bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {sending ? <Loader2 size={16} className="animate-spin" /> : null}
                        {sending ? 'Duke dërguar...' : 'Dërgo me email'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default EmailPicker
