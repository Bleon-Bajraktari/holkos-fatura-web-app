import { useMemo, useState, useEffect, useRef } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Plus, Search, Download, Trash2, CheckCircle2, XCircle, Copy, Mail, ArrowLeft, CheckSquare, RefreshCw, X, ChevronDown, FileText } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { InvoiceService, SettingsService, CompanyService, openPdf } from '../services/api'
import { OfflineService } from '../services/offline'
import EmailPicker from '../components/EmailPicker'
import ConfirmDialog from '../components/ConfirmDialog'
import { SkeletonList } from '../components/Skeleton'
import { useToast } from '../hooks/useToast'

const months = [
    'Të gjithë', 'Janar', 'Shkurt', 'Mars', 'Prill', 'Maj', 'Qershor',
    'Korrik', 'Gusht', 'Shtator', 'Tetor', 'Nëntor', 'Dhjetor'
]

const AVATAR_GRADIENTS = [
    'from-violet-500 to-purple-600',
    'from-indigo-500 to-blue-600',
    'from-emerald-500 to-teal-600',
    'from-rose-500 to-pink-600',
    'from-amber-500 to-orange-600',
    'from-cyan-500 to-sky-600',
]

const GRADIENT_COLORS = [
    { bg: 'rgba(139,92,246,0.07)', border: 'rgba(139,92,246,0.22)', glow: '0 4px 24px rgba(139,92,246,0.10)' },
    { bg: 'rgba(99,102,241,0.07)', border: 'rgba(99,102,241,0.22)', glow: '0 4px 24px rgba(99,102,241,0.10)' },
    { bg: 'rgba(16,185,129,0.07)', border: 'rgba(16,185,129,0.22)', glow: '0 4px 24px rgba(16,185,129,0.10)' },
    { bg: 'rgba(244,63,94,0.07)', border: 'rgba(244,63,94,0.22)', glow: '0 4px 24px rgba(244,63,94,0.10)' },
    { bg: 'rgba(245,158,11,0.07)', border: 'rgba(245,158,11,0.22)', glow: '0 4px 24px rgba(245,158,11,0.10)' },
    { bg: 'rgba(6,182,212,0.07)', border: 'rgba(6,182,212,0.22)', glow: '0 4px 24px rgba(6,182,212,0.10)' },
]

function avatarGradient(name: string) {
    return AVATAR_GRADIENTS[(name?.charCodeAt(0) || 0) % AVATAR_GRADIENTS.length]
}

function gradientColors(name: string) {
    return GRADIENT_COLORS[(name?.charCodeAt(0) || 0) % GRADIENT_COLORS.length]
}

function initials(name: string) {
    return (name || '?').split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
}

const InvoicesPage = () => {
    const navigate = useNavigate()
    const location = useLocation()
    const toast = useToast()
    const expandHandledRef = useRef(false)
    const [invoices, setInvoices] = useState<any[]>(() => {
        try {
            const cached = localStorage.getItem('invoices_list_cache')
            return cached ? JSON.parse(cached) : []
        } catch { return [] }
    })
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [year, setYear] = useState('')
    const [month, setMonth] = useState('Të gjithë')
    const [years, setYears] = useState<string[]>([])
    const [yearsLoaded, setYearsLoaded] = useState(false)
    const [showStatus, setShowStatus] = useState(true)
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set())
    const [selectionMode, setSelectionMode] = useState(false)
    const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set())
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [company, setCompany] = useState<any>(null)
    const [statusFilter, setStatusFilter] = useState('Të gjithë')
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    const [showDateFilters, setShowDateFilters] = useState(false)
    const [actionBarStyle, setActionBarStyle] = useState<{ bottom?: string; top?: string }>({ bottom: 'calc(var(--nav-height, 60px) + 8px)' })
    const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; id?: string | number; bulk?: boolean }>({ open: false })

    useEffect(() => {
        CompanyService.get().then(setCompany).catch(() => {})
    }, [])

    const loadInvoices = (silent = false) => {
        if (!silent) setLoading(true)
        const params: any = {}
        if (debouncedSearch) params.search = debouncedSearch
        if (statusFilter !== 'Të gjithë') params.status = statusFilter === 'E Paguar' ? 'paid' : 'draft'

        if (dateFrom) params.date_from = dateFrom
        if (dateTo) params.date_to = dateTo

        if (!dateFrom && !dateTo && year) {
            if (month === 'Të gjithë') {
                params.date_from = `${year}-01-01`
                params.date_to = `${year}-12-31`
            } else {
                const monthIdx = months.indexOf(month)
                const lastDay = new Date(Number(year), monthIdx, 0).getDate()
                params.date_from = `${year}-${String(monthIdx).padStart(2, '0')}-01`
                params.date_to = `${year}-${String(monthIdx).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
            }
        }
        InvoiceService.getAll(params)
            .then(data => {
                setInvoices(data)
                if (!debouncedSearch && statusFilter === 'Të gjithë' && !dateFrom && !dateTo) {
                    try { localStorage.setItem('invoices_list_cache', JSON.stringify(data)) } catch {}
                }
            })
            .catch(err => {
                console.error('Error loading invoices:', err)
                toast.error('Gabim gjatë ngarkimit të faturave: ' + (err.response?.data?.detail || err.message))
            })
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        SettingsService.getPaymentStatus().then(data => setShowStatus(data.enabled)).catch(() => setShowStatus(true))
        InvoiceService.getYears().then(data => {
            const yrs = data.years || []
            setYears(yrs)
            if (yrs.length) {
                const latest = String(Math.max(...yrs.map((y: string) => parseInt(y, 10))))
                setYear(latest)
            }
            setYearsLoaded(true)
        }).catch(() => { setYears([]); setYearsLoaded(true) })

        const updateActionBarPosition = () => {
            if (window.visualViewport) {
                const viewport = window.visualViewport
                const viewportHeight = viewport.height
                const windowHeight = window.innerHeight
                const viewportTop = viewport.offsetTop
                const keyboardHeight = windowHeight - viewportHeight
                if (keyboardHeight > 150) {
                    setActionBarStyle({ bottom: `${keyboardHeight + 16}px` })
                } else {
                    const bottomOffset = windowHeight - (viewportTop + viewportHeight) + 16
                    setActionBarStyle({ bottom: `${Math.max(16, bottomOffset)}px` })
                }
            } else {
                setActionBarStyle({ bottom: 'calc(var(--nav-height, 60px) + 8px)' })
            }
        }
        updateActionBarPosition()
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', updateActionBarPosition)
            window.visualViewport.addEventListener('scroll', updateActionBarPosition)
        }
        window.addEventListener('resize', updateActionBarPosition)
        return () => {
            if (window.visualViewport) {
                window.visualViewport.removeEventListener('resize', updateActionBarPosition)
                window.visualViewport.removeEventListener('scroll', updateActionBarPosition)
            }
            window.removeEventListener('resize', updateActionBarPosition)
        }
    }, [])

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedSearch(search), 400)
        return () => clearTimeout(timer)
    }, [search])

    useEffect(() => {
        if (!yearsLoaded) return
        // If we have cached data and no filters, show cached and load silently
        const hasCached = invoices.length > 0
        const hasFilters = debouncedSearch || statusFilter !== 'Të gjithë' || dateFrom || dateTo
        if (hasCached && !hasFilters) {
            loadInvoices(true)  // silent refresh — don't show skeleton
        } else {
            loadInvoices()
        }
    }, [yearsLoaded, debouncedSearch, year, month, statusFilter, dateFrom, dateTo])

    // Auto-expand client group when navigating from Dashboard activity
    useEffect(() => {
        const expandId = location.state?.expandId
        if (!expandId || expandHandledRef.current || invoices.length === 0) return
        const target = invoices.find((inv: any) =>
            inv.id === expandId || String(inv.id) === String(expandId)
        )
        if (!target) return
        expandHandledRef.current = true
        const clientName = (String(target?.client?.name ?? '')).trim() || 'Pa Emër'
        setExpandedClients(prev => { const s = new Set(prev); s.add(clientName); return s })
        setTimeout(() => {
            document.getElementById(`invoice-${target.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }, 350)
    }, [invoices, location.state?.expandId])

    const grouped = useMemo(() => {
        const sorted = [...invoices].sort((a, b) => {
            const isTempA = String(a.id).startsWith('temp-')
            const isTempB = String(b.id).startsWith('temp-')
            if (isTempA && !isTempB) return -1
            if (!isTempA && isTempB) return 1
            return (Number(b.id) || 0) - (Number(a.id) || 0)
        })
        const map: Record<string, { invoices: any[], total: number, paidTotal: number }> = {}
        for (const inv of sorted) {
            const name = (String(inv?.client?.name ?? '')).trim() || 'Pa Emër'
            if (!map[name]) map[name] = { invoices: [], total: 0, paidTotal: 0 }
            map[name].invoices.push(inv)
            map[name].total += Number(inv.total || 0)
            if (inv.status === 'paid') map[name].paidTotal += Number(inv.total || 0)
        }
        return map
    }, [invoices])

    const hasActiveFilters = statusFilter !== 'Të gjithë' || dateFrom || dateTo

    const toggleClient = (name: string) => {
        setExpandedClients(prev => {
            const next = new Set(prev)
            if (next.has(name)) next.delete(name)
            else next.add(name)
            return next
        })
    }

    const handleReset = () => {
        setSearch('')
        setYear(years.length ? String(Math.max(...years.map(y => parseInt(y, 10)))) : '')
        setMonth('Të gjithë')
        setStatusFilter('Të gjithë')
        setDateFrom('')
        setDateTo('')
    }

    const toggleSelect = (id: string | number) => {
        if (!selectionMode) return
        setSelectedIds(prev => {
            const next = new Set(prev)
            if (next.has(id)) next.delete(id)
            else next.add(id)
            return next
        })
    }

    const clearSelection = () => {
        setSelectedIds(new Set())
        setSelectionMode(false)
    }

    const selectAll = () => {
        if (selectedIds.size === invoices.length && invoices.length > 0) {
            setSelectedIds(new Set())
        } else {
            setSelectedIds(new Set(invoices.map(inv => inv.id)))
        }
    }

    const toggleSelectionMode = () => {
        setSelectionMode(prev => !prev)
        if (selectionMode) setSelectedIds(new Set())
    }

    const handleDownloadPdf = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            toast.warning('Fatura nuk është sinkronizuar ende. Prisni sa të ketë internet.')
            return
        }
        try {
            await openPdf(`/invoices/${id}/pdf`)
        } catch (e) {
            toast.error('Gabim gjatë hapjes së PDF: ' + ((e as any)?.response?.data?.detail || (e as Error)?.message))
        }
    }

    const handleDelete = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            await OfflineService.removePendingDocument('invoices', String(id))
            loadInvoices()
            return
        }
        try {
            await InvoiceService.delete(Number(id))
            toast.success('Fatura u fshi me sukses')
            loadInvoices()
        } catch {
            toast.error('Gabim gjatë fshirjes së faturës')
        }
    }

    const handleToggleStatus = async (id: string | number, current: string) => {
        if (String(id).startsWith('temp-')) return
        const next = current === 'paid' ? 'draft' : 'paid'
        try {
            await InvoiceService.updateStatus(Number(id), next)
            toast.success(next === 'paid' ? 'Fatura u shënua si e paguar' : 'Fatura u shënua si e papaguar')
            loadInvoices()
        } catch {
            toast.error('Gabim gjatë ndryshimit të statusit')
        }
    }

    const handleClone = (id: string | number) => {
        navigate(`/invoices/new?clone=${id}`)
    }

    const handleBulkDelete = async () => {
        const validIds = Array.from(selectedIds).filter(id => typeof id === 'number') as number[]
        if (validIds.length === 0) return
        try {
            await InvoiceService.bulkDelete(validIds)
            toast.success(`${validIds.length} fatura u fshinë`)
            clearSelection()
            loadInvoices()
        } catch {
            toast.error('Gabim gjatë fshirjes në masë')
        }
    }

    const handleBulkEmail = async (overrideEmail?: string) => {
        if (!selectedIds.size) return
        const validIds = Array.from(selectedIds).filter(id => typeof id === 'number') as number[]
        if (validIds.length === 0) return
        const useSmtp = company?.smtp_user && company?.smtp_password && import.meta.env.PROD && !window.location.hostname.includes('localhost')
        if (useSmtp && overrideEmail) {
            await InvoiceService.bulkEmailViaSmtp(validIds, overrideEmail, company)
        } else {
            await InvoiceService.bulkEmail(validIds, overrideEmail)
        }
        clearSelection()
        loadInvoices()
    }

    const statusChips = ['Të gjithë', 'E Paguar', 'E Papaguar']

    return (
        <div className="min-h-screen pb-28">
            {/* Sticky Header */}
            <div className="bg-card/95 backdrop-blur-xl border-b border-border sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 min-w-0">
                            <button onClick={() => navigate('/')} className="btn-icon shrink-0">
                                <ArrowLeft size={18} />
                            </button>
                            <div className="min-w-0">
                                <h1 className="text-lg sm:text-xl font-black text-foreground tracking-tight leading-none">
                                    Lista e <span className="text-primary">Faturave</span>
                                </h1>
                                <p className="text-[11px] text-muted-foreground font-medium mt-0.5 hidden sm:block">
                                    {invoices.length} fatura gjithsej
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button onClick={() => loadInvoices()} title="Rifresko" className="btn-icon shrink-0">
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <button
                                onClick={toggleSelectionMode}
                                className={`btn-icon shrink-0 ${selectionMode ? 'text-primary bg-primary/10 border-primary/30' : ''}`}
                                title="Selekto"
                            >
                                <CheckSquare size={16} />
                            </button>
                            <Link to="/invoices/new" className="hidden sm:block">
                                <button className="btn-primary flex items-center gap-2 px-4 py-2.5 text-sm">
                                    <Plus size={15} />
                                    <span>Faturë e Re</span>
                                </button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-3 sm:px-6 mt-3 sm:mt-6">
                {/* Search Bar */}
                <div className="search-bar mb-3">
                    <Search className="text-muted-foreground shrink-0 ml-1" size={16} />
                    <input
                        type="text"
                        placeholder="Kërko faturë, klient..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="flex-1 bg-transparent border-none outline-none px-3 text-sm font-medium text-foreground placeholder:text-muted-foreground h-full"
                    />
                    {search && (
                        <button onClick={() => setSearch('')} className="p-1.5 text-muted-foreground hover:text-foreground transition-colors mr-1">
                            <X size={14} />
                        </button>
                    )}
                </div>

                {/* Filter Chips — mobile horizontal scroll */}
                <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1 mb-3">
                    {statusChips.map(chip => (
                        <button
                            key={chip}
                            onClick={() => setStatusFilter(chip)}
                            className={`filter-chip shrink-0 ${statusFilter === chip ? 'active' : ''}`}
                        >
                            {chip}
                        </button>
                    ))}

                    <div className="w-px h-4 bg-border shrink-0 mx-1" />

                    {years.map(y => (
                        <button
                            key={y}
                            onClick={() => setYear(y)}
                            className={`filter-chip shrink-0 ${year === y ? 'active' : ''}`}
                        >
                            {y}
                        </button>
                    ))}

                    <div className="w-px h-4 bg-border shrink-0 mx-1" />

                    {months.slice(1).map((m) => (
                        <button
                            key={m}
                            onClick={() => setMonth(month === m ? 'Të gjithë' : m)}
                            className={`filter-chip shrink-0 ${month === m ? 'active' : ''}`}
                        >
                            {m}
                        </button>
                    ))}
                </div>

                {/* Advanced filters toggle */}
                <div className="flex items-center justify-between mb-3">
                    <button
                        onClick={() => setShowDateFilters(v => !v)}
                        className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <ChevronDown size={14} className={`transition-transform ${showDateFilters ? 'rotate-180' : ''}`} />
                        Filtrat e datës
                    </button>
                    {hasActiveFilters && (
                        <button onClick={handleReset} className="text-xs font-bold text-primary hover:text-primary/80 transition-colors flex items-center gap-1">
                            <X size={12} /> Pastro filtrat
                        </button>
                    )}
                </div>

                <AnimatePresence>
                    {showDateFilters && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden mb-3"
                        >
                            <div className="grid grid-cols-2 gap-2 p-3 card-base">
                                <div>
                                    <label className="input-label">Nga data</label>
                                    <div className="relative">
                                        <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input-base text-sm" />
                                        {dateFrom && (
                                            <button onClick={() => setDateFrom('')} className="absolute right-2 top-1/2 -translate-y-1/2">
                                                <X size={12} className="text-muted-foreground" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                                <div>
                                    <label className="input-label">Deri më</label>
                                    <div className="relative">
                                        <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input-base text-sm" />
                                        {dateTo && (
                                            <button onClick={() => setDateTo('')} className="absolute right-2 top-1/2 -translate-y-1/2">
                                                <X size={12} className="text-muted-foreground" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Content */}
                {loading ? (
                    <SkeletonList count={5} />
                ) : Object.keys(grouped).length === 0 ? (
                    <div className="card-base p-16 text-center">
                        <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <FileText size={28} className="text-muted-foreground/50" />
                        </div>
                        <h3 className="text-base font-bold text-foreground">Nuk u gjetën fatura</h3>
                        <p className="text-sm text-muted-foreground mt-1">Provo të ndryshosh filtrat.</p>
                        <Link to="/invoices/new" className="inline-block mt-4">
                            <button className="btn-primary px-5 py-2.5 text-sm flex items-center gap-2 mx-auto">
                                <Plus size={15} /> Faturë e Re
                            </button>
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {Object.entries(grouped).map(([clientName, group]) => {
                            const isExpanded = expandedClients.has(clientName)
                            const grad = avatarGradient(clientName)
                            const colors = gradientColors(clientName)
                            const paidCount = group.invoices.filter((inv: any) => inv.status === 'paid').length
                            const paidRatio = group.total > 0 ? group.paidTotal / group.total : 0

                            return (
                                <div
                                    key={clientName}
                                    className="rounded-2xl overflow-hidden transition-all duration-300"
                                    style={{
                                        background: isExpanded ? colors.bg : 'transparent',
                                        border: `1px solid ${isExpanded ? colors.border : 'hsl(var(--border))'}`,
                                        boxShadow: isExpanded ? colors.glow : 'none',
                                    }}
                                >
                                    {/* Client Header */}
                                    <button
                                        onClick={() => toggleClient(clientName)}
                                        className="w-full flex items-center gap-3 px-4 py-4 text-left transition-colors hover:bg-muted/20"
                                    >
                                        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center shrink-0 shadow-md`}>
                                            <span className="text-xs font-black text-white">{initials(clientName)}</span>
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1.5">
                                                <span className="text-sm font-black text-foreground uppercase tracking-wide truncate">{clientName}</span>
                                                <span className="shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-muted/80 text-muted-foreground border border-border/50">
                                                    {group.invoices.length}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 h-1.5 bg-muted/60 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                                                        style={{ width: `${paidRatio * 100}%` }}
                                                    />
                                                </div>
                                                <span className="text-[10px] font-bold text-muted-foreground shrink-0">
                                                    {paidCount}/{group.invoices.length} pag.
                                                </span>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2 shrink-0">
                                            <span className="text-sm font-black text-foreground mono">
                                                {group.total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                            </span>
                                            <ChevronDown
                                                size={15}
                                                className={`text-muted-foreground transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                                            />
                                        </div>
                                    </button>

                                    {/* Invoice Mini-Cards */}
                                    <AnimatePresence initial={false}>
                                        {isExpanded && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: 'auto', opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                transition={{ duration: 0.25, ease: 'easeInOut' }}
                                                className="overflow-hidden"
                                            >
                                                <div className="px-3 pb-3 space-y-2">
                                                    {group.invoices.map((inv: any, idx: number) => {
                                                        const isSelected = selectedIds.has(inv.id)
                                                        const isPending = inv.status === 'pending-sync' || inv._isOfflinePending
                                                        const isPaid = inv.status === 'paid'

                                                        return (
                                                            <motion.div
                                                                key={inv.id}
                                                                id={`invoice-${inv.id}`}
                                                                initial={{ opacity: 0, y: 6 }}
                                                                animate={{ opacity: 1, y: 0 }}
                                                                transition={{ delay: idx * 0.04, duration: 0.2 }}
                                                                onClick={() => selectionMode && toggleSelect(inv.id)}
                                                                className={`rounded-xl border p-3 transition-all ${
                                                                    selectionMode && isSelected
                                                                        ? 'bg-primary/5 border-primary/40 cursor-pointer'
                                                                        : selectionMode
                                                                            ? 'bg-card/80 border-border/60 cursor-pointer'
                                                                            : 'bg-card/80 border-border/60 backdrop-blur-sm'
                                                                }`}
                                                            >
                                                                {/* Invoice info row */}
                                                                <div className="flex items-start justify-between gap-2 mb-2.5">
                                                                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                                                                        {selectionMode && (
                                                                            <div className={`w-4 h-4 shrink-0 rounded border-2 flex items-center justify-center transition-all ${isSelected ? 'bg-primary border-primary' : 'border-muted-foreground/40'}`}>
                                                                                {isSelected && <CheckSquare size={9} className="text-white" />}
                                                                            </div>
                                                                        )}
                                                                        <span className="text-sm font-black text-foreground mono">{inv.invoice_number}</span>
                                                                        {showStatus && !isPending && (
                                                                            <span className={isPaid ? 'badge-base badge-paid' : 'badge-base badge-unpaid'}>
                                                                                {isPaid ? 'E PAGUAR' : 'E PAPAGUAR'}
                                                                            </span>
                                                                        )}
                                                                        {isPending && (
                                                                            <span className="badge-base badge-pending">
                                                                                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse" />
                                                                                PRITJE
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <div className="text-right shrink-0">
                                                                        <div className="text-base font-black text-foreground mono leading-none">
                                                                            {parseFloat(inv.total).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                                                        </div>
                                                                        <div className="text-[10px] text-muted-foreground font-medium mt-0.5 mono">
                                                                            {new Date(inv.date).toLocaleDateString('sq-AL')} · TVSh {parseFloat(inv.vat_percentage ?? 0).toFixed(0)}%
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                {/* Action buttons — always visible */}
                                                                {!selectionMode && (
                                                                    <div className="flex items-center gap-1.5 pt-2 border-t border-border/40">
                                                                        <div className={`flex-1 grid gap-1.5 ${showStatus ? 'grid-cols-4' : 'grid-cols-3'}`}>
                                                                            <Link to={`/invoices/edit/${inv.id}`} className="contents">
                                                                                <button className="btn-primary w-full py-1.5 text-[10px] font-bold flex items-center justify-center gap-1">
                                                                                    Ndrysho
                                                                                </button>
                                                                            </Link>
                                                                            <button onClick={() => handleDownloadPdf(inv.id)} className="btn-icon w-full py-1.5 text-[10px] flex items-center justify-center gap-1">
                                                                                <Download size={11} /> PDF
                                                                            </button>
                                                                            <button onClick={() => handleClone(inv.id)} className="btn-icon w-full py-1.5 text-[10px] flex items-center justify-center gap-1">
                                                                                <Copy size={11} /> Klon
                                                                            </button>
                                                                            {showStatus && (
                                                                                <button
                                                                                    onClick={() => handleToggleStatus(inv.id, inv.status)}
                                                                                    className={`w-full py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 transition-all ${
                                                                                        isPaid
                                                                                            ? 'bg-rose-100 text-rose-700 hover:bg-rose-200 dark:bg-rose-950/40 dark:text-rose-400'
                                                                                            : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400'
                                                                                    }`}
                                                                                >
                                                                                    <CheckCircle2 size={11} />
                                                                                    {isPaid ? 'Pa pag.' : 'Paguar'}
                                                                                </button>
                                                                            )}
                                                                        </div>
                                                                        <button
                                                                            onClick={() => setConfirmDialog({ open: true, id: inv.id })}
                                                                            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                                                                        >
                                                                            <Trash2 size={14} />
                                                                        </button>
                                                                    </div>
                                                                )}
                                                            </motion.div>
                                                        )
                                                    })}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* Mobile FAB — New Invoice */}
            {!selectionMode && (
                <Link
                    to="/invoices/new"
                    className="fixed right-4 z-40 lg:hidden"
                    style={{ bottom: 'calc(var(--nav-height, 60px) + 16px)' }}
                >
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="w-13 h-13 rounded-2xl btn-primary flex items-center justify-center shadow-xl shadow-primary/30"
                        style={{ width: 52, height: 52 }}
                    >
                        <Plus size={22} />
                    </motion.button>
                </Link>
            )}

            {/* Selection Bar */}
            <AnimatePresence>
                {selectionMode && (
                    <motion.div
                        initial={{ y: 80, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: 80, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="fixed left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] sm:max-w-md glass border border-border rounded-2xl shadow-2xl px-5 py-3.5"
                        style={actionBarStyle}
                    >
                        <div className="flex items-center justify-between gap-3">
                            <div>
                                <div className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Të zgjedhura</div>
                                <div className="text-xl font-black text-primary mono">{selectedIds.size}</div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={selectAll} className="btn-icon" title="Selekto të gjitha">
                                    <CheckSquare size={18} />
                                </button>
                                {selectedIds.size > 0 && (
                                    <>
                                        <button onClick={() => setEmailModalOpen(true)} className="btn-primary flex items-center gap-1.5 px-3 py-2 text-sm">
                                            <Mail size={15} /> Email
                                        </button>
                                        <button
                                            onClick={() => setConfirmDialog({ open: true, bulk: true })}
                                            className="btn-danger flex items-center gap-1.5 px-3 py-2 text-sm"
                                        >
                                            <Trash2 size={15} /> Fshi
                                        </button>
                                    </>
                                )}
                                <button onClick={clearSelection} className="btn-icon">
                                    <XCircle size={18} />
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <EmailPicker
                isOpen={emailModalOpen}
                title="Dërgo faturat me email"
                onClose={() => setEmailModalOpen(false)}
                onConfirm={(email) => handleBulkEmail(email)}
            />

            <ConfirmDialog
                isOpen={confirmDialog.open}
                title={confirmDialog.bulk ? 'Fshi faturat' : 'Fshi faturën'}
                message={confirmDialog.bulk
                    ? `A jeni të sigurt se doni të fshini ${selectedIds.size} fatura? Ky veprim është i pakthyeshëm.`
                    : 'A jeni të sigurt se doni të fshini këtë faturë? Ky veprim është i pakthyeshëm.'
                }
                confirmLabel="Fshi"
                onConfirm={() => {
                    if (confirmDialog.bulk) handleBulkDelete()
                    else if (confirmDialog.id != null) handleDelete(confirmDialog.id)
                    setConfirmDialog({ open: false })
                }}
                onCancel={() => setConfirmDialog({ open: false })}
            />
        </div>
    )
}

export default InvoicesPage
