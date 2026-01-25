import { useMemo, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, ArrowLeft, Copy, Mail, XCircle, CheckSquare, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { OfferService } from '../services/api'
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
    const [year, setYear] = useState(new Date().getFullYear().toString())
    const [month, setMonth] = useState('Të gjithë')
    const [years, setYears] = useState<string[]>([])
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
    const [selectionMode, setSelectionMode] = useState(false)
    const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set())
    const [expandedOfferId, setExpandedOfferId] = useState<number | null>(null)
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [actionBarStyle, setActionBarStyle] = useState<{ bottom?: string; top?: string }>({ bottom: '64px' })

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
        OfferService.getYears().then(data => setYears(data.years || [])).catch(() => setYears([]))

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
                setActionBarStyle({ bottom: '64px' })
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
        loadOffers()
    }, [debouncedSearch, year, month, dateFrom, dateTo])

    const grouped = useMemo(() => {
        const map: Record<string, { offers: any[], total: number }> = {}
        for (const off of offers) {
            const name = off.client?.name?.trim() || 'Pa Emër'
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
        setYear(new Date().getFullYear().toString())
        setMonth('Të gjithë')
        setDateFrom('')
        setDateTo('')
    }

    const toggleOfferActions = (id: number) => {
        setExpandedOfferId(prev => (prev === id ? null : id))
    }

    const toggleSelect = (id: number) => {
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

    const handleDownloadPdf = (id: number) => {
        const isMobile = window.matchMedia('(max-width: 768px)').matches || /iPhone|iPad|iPod/i.test(navigator.userAgent)
        if (isMobile) {
            window.location.href = `/api/offers/${id}/pdf`
        } else {
            window.open(`/api/offers/${id}/pdf`, '_blank', 'noopener,noreferrer')
        }
    }

    const handleGeneratePdf = async (id: number) => {
        try {
            const isMobile = window.matchMedia('(max-width: 768px)').matches || /iPhone|iPad|iPod/i.test(navigator.userAgent)
            if (isMobile) {
                window.location.href = `/api/offers/${id}/pdf`
            } else {
                window.open(`/api/offers/${id}/pdf`, '_blank', 'noopener,noreferrer')
            }
            setTimeout(() => loadOffers(), 1000)
        } catch (error) {
            console.error('Error generating PDF:', error)
            alert('Gabim gjatë gjenerimit të PDF!')
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm('A jeni të sigurt?')) return
        await OfferService.delete(id)
        loadOffers()
    }

    const handleClone = (id: number) => {
        navigate(`/offers/new?clone=${id}`)
    }

    const handleBulkDelete = async () => {
        if (!selectedIds.size) return
        if (!confirm(`A jeni të sigurt se doni të fshini ${selectedIds.size} oferta?`)) return
        await OfferService.bulkDelete(Array.from(selectedIds))
        clearSelection()
        loadOffers()
    }

    const handleBulkEmail = async (overrideEmail?: string) => {
        if (!selectedIds.size) return
        try {
            await OfferService.bulkEmail(Array.from(selectedIds), overrideEmail)
            clearSelection()
            loadOffers()
        } catch (err: any) {
            alert(err?.response?.data?.detail || 'Gabim gjatë dërgimit të email-it.')
        }
    }

    return (
        <div className="min-h-screen pb-12">
            {/* Header Section */}
            <div className="bg-white border-b border-gray-100 sticky top-0 z-30 transition-all duration-300">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-2 sm:py-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 sm:gap-6">
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => navigate('/')}
                                className="p-2 bg-gray-50 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-300 active:scale-95"
                            >
                                <ArrowLeft size={18} />
                            </button>
                            <div>
                                <h1 className="text-lg sm:text-2xl font-black text-gray-900 tracking-tight leading-none sm:leading-normal">Lista e <span className="gradient-text">Ofertave</span></h1>
                                <p className="text-gray-500 text-[10px] sm:text-sm font-medium">Menaxhoni ofertat tuaja</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={loadOffers}
                                className="p-2.5 bg-gray-50 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-300 active:scale-95 sm:flex hidden"
                            >
                                <CheckSquare size={18} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <Link to="/offers/new" className="w-full sm:w-auto">
                                <button className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white px-4 py-2 sm:px-6 sm:py-3 rounded-xl sm:rounded-2xl font-bold text-xs sm:text-sm shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 w-full">
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
                <div className="glass p-2 sm:p-5 rounded-2xl sm:rounded-[2.5rem] mb-3 sm:mb-8 shadow-xl shadow-blue-500/5 border-white/40">
                    <div className="flex flex-col gap-2 sm:gap-5">
                        {/* Search Row */}
                        <div className="flex items-center bg-gray-50/50 border border-gray-100/80 rounded-xl px-3 sm:px-5 h-10 sm:h-14 group focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 focus-within:bg-white transition-all shadow-inner">
                            <Search className="text-gray-400 group-focus-within:text-blue-500 transition-colors shrink-0" size={16} />
                            <input
                                type="text"
                                placeholder="Kërko oferte, klientin..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="flex-1 bg-transparent border-none outline-none pl-2 sm:pl-4 text-xs sm:text-[16px] font-medium h-full w-full"
                            />
                        </div>

                        {/* Filters Row */}
                        <div className="grid grid-cols-12 gap-1.5 sm:gap-4">
                            <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                                <label className="text-[8px] font-black text-gray-400 uppercase tracking-widest ml-2 mb-0.5 block text-center">Viti</label>
                                <select
                                    value={year}
                                    onChange={e => setYear(e.target.value)}
                                    className="w-full bg-white/50 border border-gray-100 rounded-lg sm:rounded-xl h-9 sm:h-11 py-1.5 sm:py-0 px-1 sm:px-2 text-[11px] sm:text-xs font-semibold text-gray-700 focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none outline-none text-center"
                                >
                                    <option value="">Viti</option>
                                    {years.map(y => <option key={y} value={y}>{y}</option>)}
                                </select>
                            </div>
                            <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                                <label className="text-[8px] font-black text-gray-400 uppercase tracking-widest ml-2 mb-0.5 block text-center">Muaji</label>
                                <select
                                    value={month}
                                    onChange={e => setMonth(e.target.value)}
                                    className="w-full bg-white/50 border border-gray-100 rounded-lg sm:rounded-xl h-9 sm:h-11 py-1.5 sm:py-0 px-2 sm:px-3 text-[11px] sm:text-xs font-semibold text-gray-700 focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none outline-none text-center"
                                >
                                    {months.map(m => <option key={m} value={m}>{m}</option>)}
                                </select>
                            </div>
                            <div className="col-span-6 lg:col-span-3">
                                <label className="text-[8px] font-black text-gray-400 uppercase tracking-widest ml-2 mb-0.5 block text-center">Nga data</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={dateFrom}
                                        onChange={e => setDateFrom(e.target.value)}
                                        className="w-full bg-white/50 border border-gray-100 rounded-lg sm:rounded-xl h-9 sm:h-11 px-2 sm:px-3 pr-8 sm:pr-10 text-[11px] font-medium focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none outline-none text-center"
                                    />
                                    {dateFrom && (
                                        <button
                                            onClick={() => setDateFrom('')}
                                            className="absolute right-1 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                                        >
                                            <X size={12} className="text-gray-400" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-6 lg:col-span-3">
                                <label className="text-[8px] font-black text-gray-400 uppercase tracking-widest ml-2 mb-0.5 block text-center">Deri më</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={dateTo}
                                        onChange={e => setDateTo(e.target.value)}
                                        className="w-full bg-white/50 border border-gray-100 rounded-lg sm:rounded-xl h-9 sm:h-11 px-2 sm:px-3 pr-8 sm:pr-10 text-[11px] font-medium focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none outline-none text-center"
                                    />
                                    {dateTo && (
                                        <button
                                            onClick={() => setDateTo('')}
                                            className="absolute right-1 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                                        >
                                            <X size={12} className="text-gray-400" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-6 lg:col-span-1 flex items-end">
                                <button
                                    onClick={handleReset}
                                    className="h-9 sm:h-11 w-full rounded-lg sm:rounded-xl text-[9px] sm:text-[10px] font-black bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all flex items-center justify-center gap-1 sm:gap-2"
                                >
                                    RESET
                                </button>
                            </div>
                            <div className="col-span-6 lg:col-span-1 flex items-end">
                                <button
                                    onClick={toggleSelectionMode}
                                    className={`h-9 sm:h-11 w-full rounded-lg sm:rounded-xl text-[9px] sm:text-[10px] font-black transition-all flex items-center justify-center gap-1 sm:gap-2 ${selectionMode
                                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                        : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50 shadow-sm'
                                        }`}
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
                        <div className="flex flex-col items-center justify-center py-24 text-gray-400 gap-4">
                            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                            <p className="font-bold animate-pulse">Duke ngarkuar ofertat...</p>
                        </div>
                    ) : Object.keys(grouped).length === 0 ? (
                        <div className="bg-white rounded-[2rem] p-16 text-center shadow-sm border border-gray-100">
                            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Search size={32} className="text-gray-300" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">Nuk u gjet asnjë ofertë</h3>
                            <p className="text-gray-500 mt-2">Provo të ndryshosh filtrat ose kërkimin tuaj.</p>
                        </div>
                    ) : (
                        Object.entries(grouped).map(([clientName, group]) => {
                            const isExpanded = expandedClients.has(clientName)
                            return (
                                <div key={clientName} className="bg-white rounded-xl sm:rounded-2xl border border-gray-100/80 overflow-hidden group/card shadow-sm hover:shadow-md transition-all duration-300">
                                    <button
                                        onClick={() => toggleClient(clientName)}
                                        className={`w-full min-h-[4rem] sm:min-h-[4.5rem] flex items-center justify-between px-3 sm:px-5 py-2.5 text-left transition-all ${isExpanded ? 'bg-gray-50/50' : 'hover:bg-gray-50/30'
                                            }`}
                                    >
                                        <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
                                            <div className="w-1 self-stretch min-h-[1.5rem] bg-blue-600 rounded-full shrink-0"></div>
                                            <div className="flex flex-col gap-y-1 min-w-0">
                                                <span className="text-[13px] sm:text-sm font-black text-gray-900 uppercase tracking-wide leading-tight break-words">{clientName}</span>
                                                <div className="flex flex-wrap items-center gap-2 sm:gap-3 shrink-0">
                                                    <span className="text-[9px] sm:text-[10px] font-bold text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded-md border border-gray-100 uppercase">{group.offers.length} oferta</span>
                                                    <div className="flex items-center gap-1 sm:gap-1.5">
                                                        <span className="text-[8px] sm:text-[9px] font-black text-gray-400 uppercase tracking-widest whitespace-nowrap">Gjithsej:</span>
                                                        <span className="text-xs sm:text-sm font-black text-blue-600 whitespace-nowrap">{group.total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={`p-1 rounded-lg bg-white border border-gray-100 text-gray-400 transition-transform duration-300 shrink-0 ${isExpanded ? 'rotate-180 bg-blue-50 text-blue-600' : ''}`}>
                                            <Plus size={12} className={isExpanded ? 'rotate-45' : ''} />
                                        </div>
                                    </button>

                                    {isExpanded && (
                                        <div className="px-8 pb-8 space-y-4 pt-2">
                                            <div className="hidden sm:grid grid-cols-12 gap-4 px-4 py-2 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] border-b border-gray-50">
                                                <div className="col-span-3">Numri & Data</div>
                                                <div className="col-span-4 text-right">Shuma</div>
                                                <div className="col-span-5 text-right">Veprimet</div>
                                            </div>
                                            {group.offers.map((off: any) => {
                                                const isSelected = selectedIds.has(off.id)
                                                const isRowExpanded = expandedOfferId === off.id
                                                const hasPdf = off.pdf_path && off.pdf_path.trim() !== ''

                                                return (
                                                    <div
                                                        key={off.id}
                                                        className={`relative overflow-hidden transition-all duration-300 ${selectionMode ? 'cursor-pointer' : ''
                                                            } ${selectionMode && isSelected
                                                                ? 'bg-blue-50/80 border-blue-200'
                                                                : 'bg-white border border-gray-100/50 hover:border-blue-100/50 shadow-sm hover:shadow-md'
                                                            } rounded-2xl`}
                                                    >
                                                        {/* Summary Row */}
                                                        <div
                                                            onClick={() => selectionMode ? toggleSelect(off.id) : toggleOfferActions(off.id)}
                                                            className="flex items-center justify-between px-4 py-2.5 sm:grid sm:grid-cols-12 sm:gap-4 cursor-pointer"
                                                        >
                                                            <div className="col-span-6 flex items-center gap-3">
                                                                {selectionMode && (
                                                                    <div className={`w-5 h-5 shrink-0 rounded-md border-2 flex items-center justify-center transition-all ${isSelected
                                                                        ? 'bg-blue-600 border-blue-600'
                                                                        : 'border-gray-200 bg-white'
                                                                        }`}>
                                                                        {isSelected && <CheckSquare size={12} className="text-white" />}
                                                                    </div>
                                                                )}
                                                                <div className="min-w-0">
                                                                    <div className="font-bold text-gray-900 text-sm truncate">{off.offer_number}</div>
                                                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">{new Date(off.date).toLocaleDateString('sq-AL')}</div>
                                                                </div>
                                                            </div>

                                                            <div className="col-span-6 text-right flex items-center justify-end gap-3">
                                                                <div className="text-sm font-black text-gray-900">{parseFloat(off.total || 0).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</div>
                                                                <div className={`p-1.5 rounded-lg bg-gray-50 text-gray-400 transition-transform duration-300 ${isRowExpanded ? 'rotate-180 bg-blue-50 text-blue-600' : ''}`}>
                                                                    <Plus size={14} className={isRowExpanded ? 'rotate-45' : ''} />
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
                                                                    className="border-t border-gray-50 bg-gray-50/30 overflow-hidden"
                                                                >
                                                                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-end gap-2">
                                                                        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                                                                            {hasPdf ? (
                                                                                <button
                                                                                    onClick={() => handleDownloadPdf(off.id)}
                                                                                    className="flex-1 sm:flex-none h-9 px-4 bg-white border border-gray-200 text-gray-600 rounded-xl text-xs font-bold hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                                                                                >
                                                                                    <Download size={16} /> PDF
                                                                                </button>
                                                                            ) : (
                                                                                <button
                                                                                    onClick={() => handleGeneratePdf(off.id)}
                                                                                    className="flex-1 sm:flex-none h-9 px-4 bg-orange-500 text-white rounded-xl text-xs font-bold hover:bg-orange-600 transition-all flex items-center justify-center gap-2 shadow-lg shadow-orange-500/20"
                                                                                >
                                                                                    <Download size={16} /> PDF
                                                                                </button>
                                                                            )}
                                                                            <Link to={`/offers/edit/${off.id}`} className="flex-1 sm:flex-none">
                                                                                <button className="w-full h-9 px-4 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20">
                                                                                    NDRYSHO
                                                                                </button>
                                                                            </Link>
                                                                            <button
                                                                                onClick={() => handleClone(off.id)}
                                                                                className="flex-1 sm:flex-none h-9 px-4 bg-amber-500 text-white rounded-xl text-xs font-bold hover:bg-amber-600 transition-all flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20"
                                                                            >
                                                                                <Copy size={16} /> KLON
                                                                            </button>
                                                                            <button
                                                                                onClick={() => handleDelete(off.id)}
                                                                                className="flex-1 sm:flex-none h-9 px-4 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-rose-500/20"
                                                                            >
                                                                                <Trash2 size={16} /> FSHI
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
                    className="fixed left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] sm:max-w-md bg-white/95 backdrop-blur-xl border border-blue-100 rounded-[2rem] shadow-2xl shadow-blue-500/20 px-6 py-4 transition-all duration-500 animate-in fade-in slide-in-from-bottom-8"
                    style={actionBarStyle}
                >
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Të zgjedhura</span>
                            <span className="text-xl font-black text-blue-600">{selectedIds.size}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={selectAll}
                                className="p-2.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-xl transition-colors"
                                title="Selekto të gjitha"
                            >
                                <CheckSquare size={20} />
                            </button>
                            {selectedIds.size > 0 && (
                                <>
                                    <button
                                        onClick={() => setEmailModalOpen(true)}
                                        className="h-11 px-4 bg-blue-600 text-white rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-blue-500/20 hover:scale-105 transition-all"
                                    >
                                        <Mail size={18} /> Email
                                    </button>
                                    <button
                                        onClick={handleBulkDelete}
                                        className="h-11 px-4 bg-rose-600 text-white rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-rose-500/20 hover:scale-105 transition-all"
                                    >
                                        <Trash2 size={18} /> Fshi
                                    </button>
                                </>
                            )}
                            <button
                                onClick={clearSelection}
                                className="p-2.5 bg-gray-100 text-gray-500 hover:bg-gray-200 rounded-xl transition-colors"
                            >
                                <XCircle size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <EmailPicker
                isOpen={emailModalOpen}
                title="Dërgo ofertat me email"
                allowClientEmail
                onClose={() => setEmailModalOpen(false)}
                onConfirm={(email) => { setEmailModalOpen(false); handleBulkEmail(email); }}
                onConfirmClientEmail={() => { setEmailModalOpen(false); handleBulkEmail(); }}
            />
        </div>
    )
}

export default OffersPage
