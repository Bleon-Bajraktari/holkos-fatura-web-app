import { useMemo, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, ArrowLeft, Copy, Mail, XCircle, CheckSquare, RefreshCw, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { OfferService, CompanyService, openPdf } from '../services/api'
import { OfflineService } from '../services/offline'
import EmailPicker from '../components/EmailPicker'

const months = [
    'Të gjithë', 'Janar', 'Shkurt', 'Mars', 'Prill', 'Maj', 'Qershor',
    'Korrik', 'Gusht', 'Shtator', 'Tetor', 'Nëntor', 'Dhjetor'
]

const OffersPage = () => {
    const navigate = useNavigate()
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
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [company, setCompany] = useState<any>(null)
    const [actionBarStyle, setActionBarStyle] = useState<{ bottom?: string; top?: string }>({ bottom: 'calc(var(--nav-height, 60px) + 8px)' })

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
                alert('Gabim gjatë ngarkimit të ofertave: ' + (err.response?.data?.detail || err.message))
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
        const timer = setTimeout(() => {
            setDebouncedSearch(search)
        }, 400)
        return () => clearTimeout(timer)
    }, [search])

    useEffect(() => {
        if (!yearsLoaded) return
        loadOffers()
    }, [yearsLoaded, debouncedSearch, year, month, dateFrom, dateTo])

    const grouped = useMemo(() => {
        const sorted = [...offers].sort((a, b) => {
            const idA = a.id;
            const idB = b.id;
            const isTempA = String(idA).startsWith('temp-');
            const isTempB = String(idB).startsWith('temp-');

            if (isTempA && !isTempB) return -1;
            if (!isTempA && isTempB) return 1;
            if (isTempA && isTempB) return 0;

            return (Number(idB) || 0) - (Number(idA) || 0);
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
        if (selectionMode) {
            setSelectedIds(new Set())
        }
    }

    const handleDownloadPdf = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            alert('Oferta nuk është sinkronizuar ende. Prisni sa të ketë internet për të shkarkuar PDF.');
            return;
        }
        try {
            await openPdf(`/offers/${id}/pdf`);
        } catch (e) {
            alert('Gabim gjatë hapjes së PDF: ' + (e as any)?.response?.data?.detail || (e as Error)?.message);
        }
    }

    const handleGeneratePdf = async (id: string | number) => {
        if (String(id).startsWith('temp-')) {
            alert('Oferta nuk është sinkronizuar ende.');
            return;
        }
        try {
            await openPdf(`/offers/${id}/pdf`);
            setTimeout(() => loadOffers(), 1000)
        } catch (e) {
            alert('Gabim gjatë gjenerimit të PDF: ' + (e as any)?.response?.data?.detail || (e as Error)?.message);
        }
    }

    const handleDelete = async (id: string | number) => {
        if (!confirm('A jeni të sigurt?')) return
        if (String(id).startsWith('temp-')) {
            await OfflineService.removePendingDocument('offers', String(id))
            loadOffers()
            return
        }
        await OfferService.delete(Number(id))
        loadOffers()
    }

    const handleClone = (id: string | number) => {
        navigate(`/offers/new?clone=${id}`)
    }

    const handleBulkDelete = async () => {
        if (!selectedIds.size) return
        if (!confirm(`A jeni të sigurt se doni të fshini ${selectedIds.size} oferta?`)) return
        const validIds = Array.from(selectedIds).filter(id => typeof id === 'number') as number[];
        if (validIds.length === 0) return;
        await OfferService.bulkDelete(validIds)
        clearSelection()
        loadOffers()
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
        <div className="min-h-screen pb-12">
            {/* Header Section */}
            <div className="bg-card/95 backdrop-blur-xl border-b border-border sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-5">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 sm:gap-6">
                        <div className="flex items-center gap-3">
                            <button onClick={() => navigate('/')} className="btn-icon shrink-0">
                                <ArrowLeft size={18} />
                            </button>
                            <div>
                                <h1 className="text-lg sm:text-2xl font-black text-foreground tracking-tight leading-none sm:leading-normal">Lista e <span className="gradient-text">Ofertave</span></h1>
                                <p className="text-muted-foreground text-[10px] sm:text-sm font-medium">Menaxhoni ofertat tuaja</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button onClick={loadOffers} title="Rifresko" className="btn-icon shrink-0">
                                <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <Link to="/offers/new" className="w-full sm:w-auto">
                                <button className="btn-primary-premium w-full px-6 py-2.5 sm:py-3 text-xs sm:text-sm">
                                    <Plus size={16} />
                                    <span>Krijo Ofertë</span>
                                </button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-2 sm:px-6 mt-3 sm:mt-8">
                {/* Search and Filters Bar */}
                <div className="section-card p-3 sm:p-5 mb-3 sm:mb-8">
                    <div className="flex flex-col gap-2 sm:gap-4">
                        {/* Search Row */}
                        <div className="search-bar h-10 sm:h-12">
                            <Search className="text-muted-foreground shrink-0" size={16} />
                            <input
                                type="text"
                                placeholder="Kërko oferte, klientin..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="flex-1 bg-transparent border-none outline-none pl-2 sm:pl-3 text-xs sm:text-sm font-medium h-full w-full text-foreground placeholder:text-muted-foreground"
                            />
                        </div>

                        {/* Filters Row */}
                        <div className="grid grid-cols-12 gap-1.5 sm:gap-3">
                            <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                                <label className="input-label text-center">Viti</label>
                                <select
                                    value={year}
                                    onChange={e => setYear(e.target.value)}
                                    className="input-premium text-center text-[11px] sm:text-xs py-2 px-2"
                                >
                                    <option value="">Viti</option>
                                    {years.map(y => <option key={y} value={y}>{y}</option>)}
                                </select>
                            </div>
                            <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                                <label className="input-label text-center">Muaji</label>
                                <select
                                    value={month}
                                    onChange={e => setMonth(e.target.value)}
                                    className="input-premium text-center text-[11px] sm:text-xs py-2 px-2"
                                >
                                    {months.map(m => <option key={m} value={m}>{m}</option>)}
                                </select>
                            </div>
                            <div className="col-span-6 lg:col-span-3">
                                <label className="input-label text-center">Nga data</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={dateFrom}
                                        onChange={e => setDateFrom(e.target.value)}
                                        className="input-premium text-center text-[11px] sm:text-xs py-2 pr-8"
                                    />
                                    {dateFrom && (
                                        <button onClick={() => setDateFrom('')} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-muted rounded-lg transition-colors">
                                            <X size={12} className="text-muted-foreground" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-6 lg:col-span-3">
                                <label className="input-label text-center">Deri më</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={dateTo}
                                        onChange={e => setDateTo(e.target.value)}
                                        className="input-premium text-center text-[11px] sm:text-xs py-2 pr-8"
                                    />
                                    {dateTo && (
                                        <button onClick={() => setDateTo('')} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-muted rounded-lg transition-colors">
                                            <X size={12} className="text-muted-foreground" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-6 lg:col-span-1 flex items-end">
                                <button onClick={handleReset} className="btn-secondary-premium w-full py-2 text-[9px] sm:text-[10px]">
                                    RESET
                                </button>
                            </div>
                            <div className="col-span-6 lg:col-span-1 flex items-end">
                                <button
                                    onClick={toggleSelectionMode}
                                    className={`w-full py-2 rounded-xl text-[9px] sm:text-[10px] font-black transition-all flex items-center justify-center gap-1 border ${selectionMode
                                        ? 'bg-primary text-primary-foreground border-primary shadow-md shadow-primary/25'
                                        : 'bg-muted/60 text-foreground border-border hover:bg-muted'
                                        }`}
                                    style={{ minHeight: '44px' }}
                                >
                                    {selectionMode ? <CheckSquare size={14} /> : null}
                                    {selectionMode ? 'ANULO' : 'SELEKTO'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Content Section */}
                <div className="space-y-2 sm:space-y-3">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-24 text-muted-foreground gap-4">
                            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                            <p className="font-bold animate-pulse">Duke ngarkuar ofertat...</p>
                        </div>
                    ) : Object.keys(grouped).length === 0 ? (
                        <div className="section-card p-16 text-center">
                            <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Search size={32} className="text-muted-foreground/40" />
                            </div>
                            <h3 className="text-xl font-bold text-foreground">Nuk u gjet asnjë ofertë</h3>
                            <p className="text-muted-foreground mt-2">Provo të ndryshosh filtrat ose kërkimin tuaj.</p>
                        </div>
                    ) : (
                        Object.entries(grouped).map(([clientName, group]) => {
                            const isExpanded = expandedClients.has(clientName)
                            return (
                                <div key={clientName} className="card-base overflow-hidden">
                                    <button
                                        onClick={() => toggleClient(clientName)}
                                        className={`w-full min-h-[4rem] sm:min-h-[4.5rem] flex items-center justify-between px-3 sm:px-5 py-2.5 text-left transition-all ${isExpanded ? 'bg-muted/40' : 'hover:bg-muted/30'}`}
                                    >
                                        <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
                                            <div className="w-1 self-stretch min-h-[1.5rem] bg-primary rounded-full shrink-0"></div>
                                            <div className="flex flex-col gap-y-1 min-w-0">
                                                <span className="text-[13px] sm:text-sm font-black text-foreground uppercase tracking-wide leading-tight break-words">{clientName}</span>
                                                <div className="flex flex-wrap items-center gap-2 sm:gap-3 shrink-0">
                                                    <span className="text-[9px] sm:text-[10px] font-bold text-muted-foreground bg-muted px-1.5 py-0.5 rounded-md border border-border uppercase">{group.offers.length} oferta</span>
                                                    <div className="flex items-center gap-1 sm:gap-1.5">
                                                        <span className="text-[8px] sm:text-[9px] font-black text-muted-foreground uppercase tracking-widest whitespace-nowrap">Gjithsej:</span>
                                                        <span className="text-xs sm:text-sm font-black text-primary whitespace-nowrap">{group.total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={`p-1.5 rounded-lg border transition-all duration-300 shrink-0 ${isExpanded ? 'bg-primary/10 border-primary/30 text-primary rotate-45' : 'bg-muted border-border text-muted-foreground'}`}>
                                            <Plus size={12} />
                                        </div>
                                    </button>

                                    {isExpanded && (
                                        <div className="px-4 sm:px-6 pb-6 space-y-3 pt-2">
                                            <div className="hidden sm:grid grid-cols-12 gap-4 px-4 py-2 text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] border-b border-border">
                                                <div className="col-span-4">Numri & Data</div>
                                                <div className="col-span-4 text-right">Shuma</div>
                                                <div className="col-span-4 text-right">Veprimet</div>
                                            </div>
                                            {group.offers.map((off: any) => {
                                                const isSelected = selectedIds.has(off.id)
                                                const isRowExpanded = expandedOfferId === off.id
                                                const hasPdf = off.pdf_path && off.pdf_path.trim() !== ''

                                                return (
                                                    <div
                                                        key={off.id}
                                                        className={`relative overflow-hidden transition-all duration-200 rounded-2xl border ${selectionMode ? 'cursor-pointer' : ''
                                                            } ${selectionMode && isSelected
                                                                ? 'bg-primary/5 border-primary/30'
                                                                : 'bg-muted/30 border-border hover:bg-muted/50'
                                                            }`}
                                                    >
                                                        {/* Summary Row */}
                                                        <div
                                                            onClick={() => selectionMode ? toggleSelect(off.id) : toggleOfferActions(off.id)}
                                                            className="grid grid-cols-12 gap-2 sm:gap-4 px-4 py-3 cursor-pointer items-center"
                                                        >
                                                            <div className="col-span-6 sm:col-span-4 flex items-center gap-3 min-w-0">
                                                                {selectionMode && (
                                                                    <div className={`w-5 h-5 shrink-0 rounded-md border-2 flex items-center justify-center transition-all ${isSelected ? 'bg-primary border-primary' : 'border-border bg-card'}`}>
                                                                        {isSelected && <CheckSquare size={12} className="text-white" />}
                                                                    </div>
                                                                )}
                                                                <div className="min-w-0">
                                                                    <div className="font-bold text-foreground text-sm truncate">{off.offer_number}</div>
                                                                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-tight">{new Date(off.date).toLocaleDateString('sq-AL')}</div>
                                                                </div>
                                                            </div>

                                                            <div className="col-span-4 text-right flex items-center justify-end">
                                                                {off.status === 'pending-sync' || off._isOfflinePending ? (
                                                                    <span className="status-badge-pending ml-auto">
                                                                        <div className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></div>
                                                                        PRITJE
                                                                    </span>
                                                                ) : (
                                                                    <span className="text-sm font-black text-foreground">{parseFloat(off.total || 0).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                                                                )}
                                                            </div>

                                                            <div className="col-span-2 sm:col-span-4 flex items-center justify-end">
                                                                <div className={`p-1.5 rounded-lg border transition-all duration-200 shrink-0 ${isRowExpanded ? 'bg-primary/10 border-primary/30 text-primary rotate-45' : 'bg-muted border-border text-muted-foreground'}`}>
                                                                    <Plus size={13} />
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Expanded Content */}
                                                        <AnimatePresence>
                                                            {isRowExpanded && !selectionMode && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: 'auto', opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="border-t border-border bg-muted/20 overflow-hidden"
                                                                >
                                                                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-end gap-2">
                                                                        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                                                                            {hasPdf ? (
                                                                                <button onClick={() => handleDownloadPdf(off.id)} className="btn-secondary-premium flex-1 sm:flex-none h-9 px-4 text-xs">
                                                                                    <Download size={14} /> PDF
                                                                                </button>
                                                                            ) : (
                                                                                <button onClick={() => handleGeneratePdf(off.id)} className="flex-1 sm:flex-none h-9 px-4 bg-amber-500 text-white rounded-xl text-xs font-bold hover:bg-amber-600 transition-all flex items-center justify-center gap-2">
                                                                                    <Download size={14} /> PDF
                                                                                </button>
                                                                            )}
                                                                            <Link to={`/offers/edit/${off.id}`} className="flex-1 sm:flex-none">
                                                                                <button className="btn-primary-premium w-full h-9 px-4 text-xs">NDRYSHO</button>
                                                                            </Link>
                                                                            <button onClick={() => handleClone(off.id)} className="btn-secondary-premium flex-1 sm:flex-none h-9 px-4 text-xs">
                                                                                <Copy size={14} /> KLON
                                                                            </button>
                                                                            <button onClick={() => handleDelete(off.id)} className="flex-1 sm:flex-none h-9 px-4 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition-all flex items-center justify-center gap-2">
                                                                                <Trash2 size={14} /> FSHI
                                                                            </button>
                                                                        </div>
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
                            )
                        })
                    )}
                </div>
            </div>

            {/* Selection Bar */}
            {selectionMode && (
                <div
                    className="fixed left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] sm:max-w-md bg-card/95 backdrop-blur-xl border border-border rounded-3xl shadow-2xl px-6 py-4 transition-all duration-300"
                    style={actionBarStyle}
                >
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest leading-none">Të zgjedhura</span>
                            <span className="text-xl font-black text-primary">{selectedIds.size}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <button onClick={selectAll} className="btn-icon" title="Selekto të gjitha">
                                <CheckSquare size={20} />
                            </button>
                            {selectedIds.size > 0 && (
                                <>
                                    <button onClick={() => setEmailModalOpen(true)} className="btn-primary-premium h-10 px-4 text-sm">
                                        <Mail size={16} /> Email
                                    </button>
                                    <button onClick={handleBulkDelete} className="h-10 px-4 bg-rose-600 text-white rounded-xl font-semibold text-sm flex items-center gap-2 hover:bg-rose-700 transition-all">
                                        <Trash2 size={16} /> Fshi
                                    </button>
                                </>
                            )}
                            <button onClick={clearSelection} className="btn-icon">
                                <XCircle size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <EmailPicker
                isOpen={emailModalOpen}
                title="Dërgo ofertat me email"
                onClose={() => setEmailModalOpen(false)}
                onConfirm={(email) => handleBulkEmail(email)}
            />
        </div>
    )
}

export default OffersPage
