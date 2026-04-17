import { useMemo, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, ArrowLeft, Copy, Mail, XCircle, CheckSquare, RefreshCw, X, ChevronDown, Tag, Edit2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { OfferService, CompanyService, openPdf } from '../services/api'
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

function avatarGradient(name: string) {
    return AVATAR_GRADIENTS[(name?.charCodeAt(0) || 0) % AVATAR_GRADIENTS.length]
}

function initials(name: string) {
    return (name || '?').split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
}

const OffersPage = () => {
    const navigate = useNavigate()
    const toast = useToast()
    const [offers, setOffers] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [year, setYear] = useState('')
    const [month, setMonth] = useState('Të gjithë')
    const [years, setYears] = useState<string[]>([])
    const [yearsLoaded, setYearsLoaded] = useState(false)
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set())
    const [selectionMode, setSelectionMode] = useState(false)
    const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set())
    const [expandedOfferId, setExpandedOfferId] = useState<string | number | null>(null)
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    const [showDateFilters, setShowDateFilters] = useState(false)
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [company, setCompany] = useState<any>(null)
    const [actionBarStyle, setActionBarStyle] = useState<{ bottom?: string; top?: string }>({ bottom: 'calc(var(--nav-height, 60px) + 8px)' })
    const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; id?: string | number; bulk?: boolean }>({ open: false })

    useEffect(() => {
        CompanyService.get().then(setCompany).catch(() => {})
    }, [])

    const loadOffers = () => {
        setLoading(true)
        const params: any = {}
        if (debouncedSearch) params.search = debouncedSearch

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
        OfferService.getAll(params)
            .then(data => setOffers(data))
            .catch(err => {
                console.error('Error loading offers:', err)
                toast.error('Gabim gjatë ngarkimit të ofertave: ' + (err.response?.data?.detail || err.message))
            })
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        OfferService.getYears().then(data => {
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
                    setActionBarStyle({ bottom: `${keyboardHeight + 4}px` })
                } else {
                    const bottomOffset = windowHeight - (viewportTop + viewportHeight) + 4
                    setActionBarStyle({ bottom: `${Math.max(4, bottomOffset)}px` })
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
        loadOffers()
    }, [yearsLoaded, debouncedSearch, year, month, dateFrom, dateTo])

    const grouped = useMemo(() => {
        const sorted = [...offers].sort((a, b) => {
            const isTempA = String(a.id).startsWith('temp-')
            const isTempB = String(b.id).startsWith('temp-')
            if (isTempA && !isTempB) return -1
            if (!isTempA && isTempB) return 1
            return (Number(b.id) || 0) - (Number(a.id) || 0)
        })
        const map: Record<string, { offers: any[], total: number }> = {}
        for (const off of sorted) {
            const name = (String(off?.client?.name ?? '')).trim() || 'Pa Emër'
            if (!map[name]) map[name] = { offers: [], total: 0 }
            map[name].offers.push(off)
            map[name].total += Number(off.total || 0)
        }
        return map
    }, [offers])

    const hasActiveFilters = dateFrom || dateTo

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
        setDateFrom('')
        setDateTo('')
    }

    const toggleOfferActions = (id: string | number) => {
        setExpandedOfferId(prev => (prev === id ? null : id))
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
        if (selectedIds.size === offers.length && offers.length > 0) {
            setSelectedIds(new Set())
        } else {
            setSelectedIds(new Set(offers.map(off => off.id)))
        }
    }

    const toggleSelectionMode = () => {
        setSelectionMode(prev => !prev)
        if (selectionMode) setSelectedIds(new Set())
    }

    const handleDownloadPdf = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            toast.warning('Oferta nuk është sinkronizuar ende. Prisni sa të ketë internet.')
            return
        }
        try {
            await openPdf(`/offers/${id}/pdf`)
        } catch (e) {
            toast.error('Gabim gjatë hapjes së PDF: ' + ((e as any)?.response?.data?.detail || (e as Error)?.message))
        }
    }

    const handleGeneratePdf = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            toast.warning('Oferta nuk është sinkronizuar ende.')
            return
        }
        try {
            await openPdf(`/offers/${id}/pdf`)
            setTimeout(() => loadOffers(), 1000)
        } catch (e) {
            toast.error('Gabim gjatë gjenerimit të PDF: ' + ((e as any)?.response?.data?.detail || (e as Error)?.message))
        }
    }

    const handleDelete = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            await OfflineService.removePendingDocument('offers', String(id))
            loadOffers()
            return
        }
        try {
            await OfferService.delete(Number(id))
            toast.success('Oferta u fshi me sukses')
            loadOffers()
        } catch {
            toast.error('Gabim gjatë fshirjes së ofertës')
        }
    }

    const handleClone = (id: string | number) => {
        navigate(`/offers/new?clone=${id}`)
    }

    const handleBulkDelete = async () => {
        const validIds = Array.from(selectedIds).filter(id => typeof id === 'number') as number[]
        if (validIds.length === 0) return
        try {
            await OfferService.bulkDelete(validIds)
            toast.success(`${validIds.length} oferta u fshinë`)
            clearSelection()
            loadOffers()
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
            await OfferService.bulkEmailViaSmtp(validIds, overrideEmail, company)
        } else {
            await OfferService.bulkEmail(validIds, overrideEmail)
        }
        clearSelection()
        loadOffers()
    }

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
                                    Lista e <span className="text-primary">Ofertave</span>
                                </h1>
                                <p className="text-[11px] text-muted-foreground font-medium mt-0.5 hidden sm:block">
                                    {offers.length} oferta gjithsej
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button onClick={loadOffers} title="Rifresko" className="btn-icon shrink-0">
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <button
                                onClick={toggleSelectionMode}
                                className={`btn-icon shrink-0 ${selectionMode ? 'text-primary bg-primary/10 border-primary/30' : ''}`}
                                title="Selekto"
                            >
                                <CheckSquare size={16} />
                            </button>
                            <Link to="/offers/new" className="hidden sm:block">
                                <button className="btn-primary flex items-center gap-2 px-4 py-2.5 text-sm">
                                    <Plus size={15} />
                                    <span>Ofertë e Re</span>
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
                        placeholder="Kërko ofertë, klient..."
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

                {/* Filter Chips */}
                <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1 mb-3">
                    {years.map(y => (
                        <button
                            key={y}
                            onClick={() => setYear(y)}
                            className={`filter-chip shrink-0 ${year === y ? 'active' : ''}`}
                        >
                            {y}
                        </button>
                    ))}

                    {years.length > 0 && <div className="w-px h-4 bg-border shrink-0 mx-1" />}

                    {months.slice(1).map(m => (
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
                            <Tag size={28} className="text-muted-foreground/50" />
                        </div>
                        <h3 className="text-base font-bold text-foreground">Nuk u gjetën oferta</h3>
                        <p className="text-sm text-muted-foreground mt-1">Provo të ndryshosh filtrat.</p>
                        <Link to="/offers/new" className="inline-block mt-4">
                            <button className="btn-primary px-5 py-2.5 text-sm flex items-center gap-2 mx-auto">
                                <Plus size={15} /> Ofertë e Re
                            </button>
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {Object.entries(grouped).map(([clientName, group]) => {
                            const isExpanded = expandedClients.has(clientName)
                            const grad = avatarGradient(clientName)
                            return (
                                <div key={clientName} className="card-base overflow-hidden">
                                    {/* Client Group Header */}
                                    <button
                                        onClick={() => toggleClient(clientName)}
                                        className={`w-full flex items-center justify-between px-4 py-3.5 text-left transition-all ${isExpanded ? 'bg-muted/40 border-b border-border' : 'hover:bg-muted/30'}`}
                                    >
                                        <div className="flex items-center gap-3 min-w-0 flex-1">
                                            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center shrink-0 shadow-sm`}>
                                                <span className="text-[11px] font-black text-white">{initials(clientName)}</span>
                                            </div>
                                            <div className="min-w-0">
                                                <span className="text-sm font-black text-foreground uppercase tracking-wide block truncate">{clientName}</span>
                                                <div className="flex items-center gap-2 mt-0.5">
                                                    <span className="text-[10px] font-bold text-muted-foreground">{group.offers.length} oferta</span>
                                                    <span className="text-[10px] text-muted-foreground/50">·</span>
                                                    <span className="text-[11px] font-black text-primary mono">{group.total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                                                </div>
                                            </div>
                                        </div>
                                        <ChevronDown size={16} className={`text-muted-foreground transition-transform duration-300 shrink-0 ${isExpanded ? 'rotate-180' : ''}`} />
                                    </button>

                                    {/* Offers List */}
                                    <AnimatePresence initial={false}>
                                        {isExpanded && (
                                            <motion.div
                                                initial={{ height: 0 }}
                                                animate={{ height: 'auto' }}
                                                exit={{ height: 0 }}
                                                transition={{ duration: 0.25, ease: 'easeInOut' }}
                                                className="overflow-hidden"
                                            >
                                                <div className="p-2 space-y-1.5">
                                                    {group.offers.map((off: any) => {
                                                        const isSelected = selectedIds.has(off.id)
                                                        const isRowExpanded = expandedOfferId === off.id
                                                        const hasPdf = off.pdf_path && off.pdf_path.trim() !== ''
                                                        const isPending = off.status === 'pending-sync' || off._isOfflinePending

                                                        return (
                                                            <div
                                                                key={off.id}
                                                                className={`rounded-xl border overflow-hidden transition-all duration-200 ${
                                                                    selectionMode && isSelected
                                                                        ? 'bg-primary/5 border-primary/40'
                                                                        : 'bg-background border-border hover:border-border/80 hover:bg-muted/30'
                                                                }`}
                                                            >
                                                                {/* Offer Summary Row */}
                                                                <div
                                                                    onClick={() => selectionMode ? toggleSelect(off.id) : toggleOfferActions(off.id)}
                                                                    className="flex items-center gap-3 px-3 py-3 cursor-pointer"
                                                                >
                                                                    {selectionMode && (
                                                                        <div className={`w-5 h-5 shrink-0 rounded-md border-2 flex items-center justify-center transition-all ${isSelected ? 'bg-primary border-primary' : 'border-border'}`}>
                                                                            {isSelected && <CheckSquare size={11} className="text-white" />}
                                                                        </div>
                                                                    )}

                                                                    {/* Left: number + date */}
                                                                    <div className="flex-1 min-w-0">
                                                                        <div className="flex items-center gap-2 flex-wrap">
                                                                            <span className="text-sm font-black text-foreground mono">{off.offer_number}</span>
                                                                            {isPending && (
                                                                                <span className="badge-base badge-pending">
                                                                                    <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse" />
                                                                                    PRITJE
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                        <div className="text-[11px] text-muted-foreground font-medium mt-0.5 mono">
                                                                            {new Date(off.date).toLocaleDateString('sq-AL')}
                                                                        </div>
                                                                    </div>

                                                                    {/* Right: total + expand */}
                                                                    <div className="flex items-center gap-2 shrink-0">
                                                                        {!isPending && (
                                                                            <span className="text-sm font-black text-foreground mono">
                                                                                {parseFloat(off.total || 0).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                                                            </span>
                                                                        )}
                                                                        <ChevronDown size={14} className={`text-muted-foreground transition-transform duration-200 ${isRowExpanded ? 'rotate-180' : ''}`} />
                                                                    </div>
                                                                </div>

                                                                {/* Expanded Actions */}
                                                                <AnimatePresence>
                                                                    {isRowExpanded && !selectionMode && (
                                                                        <motion.div
                                                                            initial={{ height: 0, opacity: 0 }}
                                                                            animate={{ height: 'auto', opacity: 1 }}
                                                                            exit={{ height: 0, opacity: 0 }}
                                                                            transition={{ duration: 0.18 }}
                                                                            className="border-t border-border/60 overflow-hidden"
                                                                        >
                                                                            <div className="px-3 pt-2.5 pb-3 space-y-2">
                                                                                <Link to={`/offers/edit/${off.id}`} className="block">
                                                                                    <motion.button
                                                                                        whileTap={{ scale: 0.97 }}
                                                                                        className="w-full h-8 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm shadow-violet-500/25"
                                                                                    >
                                                                                        <Edit2 size={12} />
                                                                                        Ndrysho Ofertën
                                                                                    </motion.button>
                                                                                </Link>
                                                                                <div className="grid grid-cols-3 gap-1.5">
                                                                                    <motion.button
                                                                                        whileTap={{ scale: 0.94 }}
                                                                                        onClick={() => hasPdf ? handleDownloadPdf(off.id) : handleGeneratePdf(off.id)}
                                                                                        className={`flex flex-col items-center gap-0.5 py-1.5 rounded-lg transition-colors ${
                                                                                            hasPdf
                                                                                                ? 'bg-indigo-500/10 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 active:bg-indigo-500/20'
                                                                                                : 'bg-amber-500/10 dark:bg-amber-500/15 text-amber-600 dark:text-amber-400 active:bg-amber-500/20'
                                                                                        }`}
                                                                                    >
                                                                                        <Download size={13} />
                                                                                        <span className="text-[10px] font-black tracking-wide">PDF</span>
                                                                                    </motion.button>
                                                                                    <motion.button
                                                                                        whileTap={{ scale: 0.94 }}
                                                                                        onClick={() => handleClone(off.id)}
                                                                                        className="flex flex-col items-center gap-0.5 py-1.5 rounded-lg bg-muted/80 text-muted-foreground transition-colors active:bg-muted"
                                                                                    >
                                                                                        <Copy size={13} />
                                                                                        <span className="text-[10px] font-black tracking-wide">Klon</span>
                                                                                    </motion.button>
                                                                                    <motion.button
                                                                                        whileTap={{ scale: 0.94 }}
                                                                                        onClick={() => setConfirmDialog({ open: true, id: off.id })}
                                                                                        className="flex flex-col items-center gap-0.5 py-1.5 rounded-lg bg-rose-500/10 dark:bg-rose-500/15 text-rose-500 dark:text-rose-400 transition-colors active:bg-rose-500/20"
                                                                                    >
                                                                                        <Trash2 size={13} />
                                                                                        <span className="text-[10px] font-black tracking-wide">Fshi</span>
                                                                                    </motion.button>
                                                                                </div>
                                                                            </div>
                                                                        </motion.div>
                                                                    )}
                                                                </AnimatePresence>
                                                            </div>
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

            {/* Mobile FAB — Ofertë e Re */}
            {!selectionMode && (
                <Link
                    to="/offers/new"
                    className="fixed right-4 z-40 lg:hidden"
                    style={{ bottom: 'calc(var(--nav-height, 60px) + 16px)' }}
                >
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="w-[52px] h-[52px] rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-xl shadow-primary/30"
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
                title="Dërgo ofertat me email"
                onClose={() => setEmailModalOpen(false)}
                onConfirm={(email) => handleBulkEmail(email)}
            />

            <ConfirmDialog
                isOpen={confirmDialog.open}
                title={confirmDialog.bulk ? 'Fshi ofertat' : 'Fshi ofertën'}
                message={confirmDialog.bulk
                    ? `A jeni të sigurt se doni të fshini ${selectedIds.size} oferta? Ky veprim është i pakthyeshëm.`
                    : 'A jeni të sigurt se doni të fshini këtë ofertë? Ky veprim është i pakthyeshëm.'
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

export default OffersPage
