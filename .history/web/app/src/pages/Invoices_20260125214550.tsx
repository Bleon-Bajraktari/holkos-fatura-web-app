import { useMemo, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, CheckCircle2, XCircle, Copy, Mail, ArrowLeft, CheckSquare, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { InvoiceService, SettingsService } from '../services/api'
import EmailPicker from '../components/EmailPicker'

const months = [
    'Të gjithë', 'Janar', 'Shkurt', 'Mars', 'Prill', 'Maj', 'Qershor',
    'Korrik', 'Gusht', 'Shtator', 'Tetor', 'Nëntor', 'Dhjetor'
]

const InvoicesPage = () => {
    const navigate = useNavigate()
    const [invoices, setInvoices] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [year, setYear] = useState(new Date().getFullYear().toString())
    const [month, setMonth] = useState('Të gjithë')
    const [years, setYears] = useState<string[]>([])
    const [showStatus, setShowStatus] = useState(true)
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
    const [selectionMode, setSelectionMode] = useState(false)
    const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set())
    const [expandedInvoiceId, setExpandedInvoiceId] = useState<number | null>(null)
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [statusFilter, setStatusFilter] = useState('Të gjithë')
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    const [actionBarStyle, setActionBarStyle] = useState<{ bottom?: string; top?: string }>({ bottom: '64px' })

    const loadInvoices = () => {
        setLoading(true)
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
            .then(data => setInvoices(data))
            .catch(err => {
                console.error('Error loading invoices:', err)
                alert('Gabim gjatë ngarkimit të faturave: ' + (err.response?.data?.detail || err.message))
            })
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        SettingsService.getPaymentStatus().then(data => setShowStatus(data.enabled)).catch(() => setShowStatus(true))
        InvoiceService.getYears().then(data => setYears(data.years || [])).catch(() => setYears([]))

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
        loadInvoices()
    }, [debouncedSearch, year, month, statusFilter, dateFrom, dateTo])

    const grouped = useMemo(() => {
        const map: Record<string, { invoices: any[], total: number }> = {}
        for (const inv of invoices) {
            const name = inv.client?.name?.trim() || 'Pa Emër'
            if (!map[name]) map[name] = { invoices: [], total: 0 }
            map[name].invoices.push(inv)
            map[name].total += Number(inv.total || 0)
        }
        return map
    }, [invoices])

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
        setStatusFilter('Të gjithë')
        setDateFrom('')
        setDateTo('')
    }

    const toggleInvoiceActions = (id: number) => {
        setExpandedInvoiceId(prev => (prev === id ? null : id))
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
        if (selectedIds.size === invoices.length && invoices.length > 0) {
            setSelectedIds(new Set())
        } else {
            setSelectedIds(new Set(invoices.map(inv => inv.id)))
        }
    }

    const toggleSelectionMode = () => {
        setSelectionMode(prev => !prev)
        if (selectionMode) {
            setSelectedIds(new Set())
        }
    }

    const handleDownloadPdf = (id: number) => {
        window.open(`/api/invoices/${id}/pdf`, '_blank', 'noopener,noreferrer')
    }

    const handleDelete = async (id: number) => {
        if (!confirm('A jeni të sigurt?')) return
        await InvoiceService.delete(id)
        loadInvoices()
    }

    const handleToggleStatus = async (id: number, current: string) => {
        const next = current === 'paid' ? 'draft' : 'paid'
        await InvoiceService.updateStatus(id, next)
        loadInvoices()
    }

    const handleClone = (id: number) => {
        navigate(`/invoices/new?clone=${id}`)
    }

    const handleBulkDelete = async () => {
        if (!selectedIds.size) return
        if (!confirm(`A jeni të sigurt se doni të fshini ${selectedIds.size} fatura?`)) return
        await InvoiceService.bulkDelete(Array.from(selectedIds))
        clearSelection()
        loadInvoices()
    }

    const handleBulkEmail = async (overrideEmail?: string) => {
        if (!selectedIds.size) return
        try {
            await InvoiceService.bulkEmail(Array.from(selectedIds), overrideEmail)
            clearSelection()
            loadInvoices()
        } catch (err: any) {
            alert(err?.response?.data?.detail || 'Gabim gjatë dërgimit të email-it.')
        }
    }

    return (
        <div className="min-h-screen pb-12">
            {/* Header Section */}
            <div className="bg-white border-b border-gray-100 sticky top-0 z-30 transition-all duration-300">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate('/')}
                                className="p-3 bg-gray-50 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-2xl transition-all duration-300 active:scale-95"
                            >
                                <ArrowLeft size={22} />
                            </button>
                            <div>
                                <h1 className="text-2xl font-black text-gray-900 tracking-tight">Menaxhimi i <span className="gradient-text">Faturave</span></h1>
                                <p className="text-gray-500 text-sm font-medium">Shikoni dhe menaxhoni të gjitha faturat tuaja</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={loadInvoices}
                                className="p-3 bg-gray-50 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-2xl transition-all duration-300 active:scale-95 sm:flex hidden"
                            >
                                <CheckSquare size={20} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <Link to="/invoices/new" className="w-full sm:w-auto">
                                <button className="btn-primary-premium w-full">
                                    <Plus size={20} />
                                    <span>Krijo Faturë</span>
                                </button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 mt-8">
                {/* Search and Filters Bar */}
                <div className="glass p-5 rounded-[2.5rem] mb-8 shadow-xl shadow-blue-500/5 border-white/40">
                    <div className="flex flex-col gap-5">
                        {/* Search Row */}
                        <div className="flex items-center bg-gray-50/50 border border-gray-100/80 rounded-2xl px-5 h-14 group focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 focus-within:bg-white transition-all shadow-inner">
                            <Search className="text-gray-400 group-focus-within:text-blue-500 transition-colors shrink-0" size={20} />
                            <input
                                type="text"
                                placeholder="Kërko sipas numrit, klientit, subjektit ose datës (p.sh 2024)..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="flex-1 bg-transparent border-none outline-none pl-4 text-[16px] font-medium h-full w-full"
                            />
                        </div>

                        {/* Filters Row */}
                        <div className="grid grid-cols-12 gap-2 sm:gap-4">
                            <div className="col-span-12 sm:col-span-4 lg:col-span-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-3 mb-1 block">Statusi</label>
                                <select
                                    value={statusFilter}
                                    onChange={e => setStatusFilter(e.target.value)}
                                    className="input-premium h-11 w-full font-bold text-gray-700 bg-white/50 text-xs px-3"
                                >
                                    <option value="Të gjithë">Të gjithë</option>
                                    <option value="E Paguar">E Paguar</option>
                                    <option value="E Papaguar">E Papaguar</option>
                                </select>
                            </div>
                            <div className="col-span-4 sm:col-span-4 lg:col-span-1">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-3 mb-1 block">Viti</label>
                                <select
                                    value={year}
                                    onChange={e => setYear(e.target.value)}
                                    className="input-premium h-11 w-full font-bold text-gray-700 bg-white/50 text-xs px-2"
                                >
                                    <option value="">Viti</option>
                                    {years.map(y => <option key={y} value={y}>{y}</option>)}
                                </select>
                            </div>
                            <div className="col-span-8 sm:col-span-4 lg:col-span-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-3 mb-1 block">Muaji</label>
                                <select
                                    value={month}
                                    onChange={e => setMonth(e.target.value)}
                                    className="input-premium h-11 w-full font-bold text-gray-700 bg-white/50 text-xs px-3"
                                >
                                    {months.map(m => <option key={m} value={m}>{m}</option>)}
                                </select>
                            </div>
                            <div className="col-span-6 lg:col-span-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-3 mb-1 block">Nga data</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={dateFrom}
                                        onChange={e => setDateFrom(e.target.value)}
                                        className="w-full bg-white/50 border border-gray-100 rounded-xl h-11 px-3 pr-10 text-[11px] font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none outline-none"
                                    />
                                    {dateFrom && (
                                        <button
                                            onClick={() => setDateFrom('')}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                                        >
                                            <X size={14} className="text-gray-400" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-6 lg:col-span-2">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-3 mb-1 block">Deri më</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={dateTo}
                                        onChange={e => setDateTo(e.target.value)}
                                        className="w-full bg-white/50 border border-gray-100 rounded-xl h-11 px-3 pr-10 text-[11px] font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none outline-none"
                                    />
                                    {dateTo && (
                                        <button
                                            onClick={() => setDateTo('')}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                                        >
                                            <X size={14} className="text-gray-400" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-6 lg:col-span-1 flex items-end">
                                <button
                                    onClick={handleReset}
                                    className="h-11 w-full rounded-xl text-[10px] font-black bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all flex items-center justify-center gap-2"
                                >
                                    RESET
                                </button>
                            </div>
                            <div className="col-span-6 lg:col-span-2 flex items-end">
                                <button
                                    onClick={toggleSelectionMode}
                                    className={`h-11 w-full rounded-xl text-[10px] font-black transition-all flex items-center justify-center gap-2 ${selectionMode
                                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                        : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50 shadow-sm'
                                        }`}
                                >
                                    {selectionMode ? <CheckSquare size={16} /> : null}
                                    {selectionMode ? 'ANULO' : 'SELEKTO'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Content Section */}
                <div className="space-y-6">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-24 text-gray-400 gap-4">
                            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                            <p className="font-bold animate-pulse">Duke ngarkuar faturat...</p>
                        </div>
                    ) : Object.keys(grouped).length === 0 ? (
                        <div className="bg-white rounded-[2rem] p-16 text-center shadow-sm border border-gray-100">
                            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Search size={32} className="text-gray-300" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">Nuk u gjet asnjë faturë</h3>
                            <p className="text-gray-500 mt-2">Provo të ndryshosh filtrat ose kërkimin tuaj.</p>
                        </div>
                    ) : (
                        Object.entries(grouped).map(([clientName, group]) => {
                            const isExpanded = expandedClients.has(clientName)
                            return (
                                <div key={clientName} className="card-premium overflow-hidden group/card shadow-blue-100/20">
                                    <button
                                        onClick={() => toggleClient(clientName)}
                                        className={`w-full flex items-center justify-between px-5 py-3 text-left transition-all ${isExpanded ? 'bg-gray-50/50' : 'hover:bg-gray-50/30'
                                            }`}
                                    >
                                        <div className="flex items-center gap-4 min-w-0 flex-1">
                                            <div className="w-1 h-8 bg-blue-600 rounded-full shrink-0"></div>
                                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 min-w-0">
                                                <span className="text-sm font-black text-gray-900 uppercase tracking-wide truncate">{clientName}</span>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-[10px] font-bold text-gray-400 bg-gray-50 px-2 py-0.5 rounded-md border border-gray-100 uppercase">{group.invoices.length} fatura</span>
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">Gjithsej:</span>
                                                        <span className="text-sm font-black text-blue-600">{group.total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={`p-1 rounded-lg bg-white border border-gray-100 text-gray-400 transition-transform duration-300 ${isExpanded ? 'rotate-180 bg-blue-50 text-blue-600' : ''}`}>
                                            <Plus size={14} className={isExpanded ? 'rotate-45' : ''} />
                                        </div>
                                    </button>

                                    {isExpanded && (
                                        <div className="px-8 pb-8 space-y-4 pt-2">
                                            <div className="hidden sm:grid grid-cols-12 gap-4 px-4 py-2 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] border-b border-gray-50">
                                                <div className="col-span-3">Numri & Data</div>
                                                <div className="col-span-2">Statusi</div>
                                                <div className="col-span-2 text-right">Shuma</div>
                                                <div className="col-span-5 text-right">Veprimet</div>
                                            </div>
                                            {group.invoices.map((inv: any) => {
                                                const isSelected = selectedIds.has(inv.id)
                                                const isRowExpanded = expandedInvoiceId === inv.id

                                                return (
                                                    <div
                                                        key={inv.id}
                                                        className={`relative overflow-hidden transition-all duration-300 ${selectionMode ? 'cursor-pointer' : ''
                                                            } ${selectionMode && isSelected
                                                                ? 'bg-blue-50/80 border-blue-200'
                                                                : 'bg-white border border-gray-100/50 hover:border-blue-100/50 shadow-sm hover:shadow-md'
                                                            } rounded-2xl`}
                                                    >
                                                        {/* Summary Row */}
                                                        <div
                                                            onClick={() => selectionMode ? toggleSelect(inv.id) : toggleInvoiceActions(inv.id)}
                                                            className="flex items-center justify-between px-4 py-2.5 sm:grid sm:grid-cols-12 sm:gap-4 cursor-pointer"
                                                        >
                                                            <div className="col-span-4 flex items-center gap-3">
                                                                {selectionMode && (
                                                                    <div className={`w-5 h-5 shrink-0 rounded-md border-2 flex items-center justify-center transition-all ${isSelected
                                                                        ? 'bg-blue-600 border-blue-600'
                                                                        : 'border-gray-200 bg-white'
                                                                        }`}>
                                                                        {isSelected && <CheckSquare size={12} className="text-white" />}
                                                                    </div>
                                                                )}
                                                                <div className="min-w-0">
                                                                    <div className="font-bold text-gray-900 text-sm truncate">{inv.invoice_number}</div>
                                                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">{new Date(inv.date).toLocaleDateString('sq-AL')}</div>
                                                                </div>
                                                            </div>

                                                            <div className="hidden sm:block col-span-3">
                                                                {showStatus ? (
                                                                    inv.status === 'paid' ? (
                                                                        <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">E PAGUAR</span>
                                                                    ) : (
                                                                        <span className="text-[10px] font-black text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full">E PAPAGUAR</span>
                                                                    )
                                                                ) : null}
                                                            </div>

                                                            <div className="col-span-5 text-right flex items-center justify-end gap-3">
                                                                <div className="text-sm font-black text-gray-900">{parseFloat(inv.total).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</div>
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
                                                                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                                                        <div className="flex flex-wrap gap-2">
                                                                            {showStatus && (
                                                                                <div className="sm:hidden w-full mb-1">
                                                                                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">Statusi</span>
                                                                                    {inv.status === 'paid' ? (
                                                                                        <span className="status-badge-paid w-fit text-[10px] py-0.5">E PAGUAR</span>
                                                                                    ) : (
                                                                                        <span className="status-badge-unpaid w-fit text-[10px] py-0.5">E PAPAGUAR</span>
                                                                                    )}
                                                                                </div>
                                                                            )}
                                                                        </div>

                                                                        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                                                                            <button
                                                                                onClick={() => handleDownloadPdf(inv.id)}
                                                                                className="flex-1 sm:flex-none h-9 px-4 bg-white border border-gray-200 text-gray-600 rounded-xl text-xs font-bold hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                                                                            >
                                                                                <Download size={16} /> PDF
                                                                            </button>
                                                                            <Link to={`/invoices/edit/${inv.id}`} className="flex-1 sm:flex-none">
                                                                                <button className="w-full h-9 px-4 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20">
                                                                                    NDRYSHO
                                                                                </button>
                                                                            </Link>
                                                                            <button
                                                                                onClick={() => handleClone(inv.id)}
                                                                                className="flex-1 sm:flex-none h-9 px-4 bg-amber-500 text-white rounded-xl text-xs font-bold hover:bg-amber-600 transition-all flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20"
                                                                            >
                                                                                <Copy size={16} /> KLON
                                                                            </button>
                                                                            {showStatus && (
                                                                                <button
                                                                                    onClick={() => handleToggleStatus(inv.id, inv.status)}
                                                                                    className={`flex-1 sm:flex-none h-9 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-lg ${inv.status === 'paid'
                                                                                        ? 'bg-rose-500 text-white shadow-rose-500/20 hover:bg-rose-600'
                                                                                        : 'bg-emerald-500 text-white shadow-emerald-500/20 hover:bg-emerald-600'
                                                                                        }`}
                                                                                >
                                                                                    <CheckCircle2 size={16} /> {inv.status === 'paid' ? 'E PAPAGUAR' : 'E PAGUAR'}
                                                                                </button>
                                                                            )}
                                                                            <button
                                                                                onClick={() => handleDelete(inv.id)}
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
                title="Dërgo faturat me email"
                allowClientEmail
                onClose={() => setEmailModalOpen(false)}
                onConfirm={(email) => { setEmailModalOpen(false); handleBulkEmail(email); }}
                onConfirmClientEmail={() => { setEmailModalOpen(false); handleBulkEmail(); }}
            />
        </div>
    )
}

export default InvoicesPage
