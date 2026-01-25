import { useMemo, useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, CheckCircle2, XCircle, Copy, Mail, ArrowLeft, CheckSquare } from 'lucide-react'
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
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [actionBarStyle, setActionBarStyle] = useState<{ bottom?: string; top?: string }>({ bottom: '64px' })

    const loadInvoices = () => {
        setLoading(true)
        const params: any = {}
        if (debouncedSearch) params.search = debouncedSearch
        if (year) {
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
    }, [debouncedSearch, year, month])

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
                <div className="glass p-4 rounded-[2rem] mb-8 flex flex-col lg:flex-row gap-4 items-center shadow-lg shadow-blue-500/5">
                    <div className="relative flex-1 w-full group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={20} />
                        <input
                            type="text"
                            placeholder="Kërko sipas numrit, klientit..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="input-premium w-full pl-12 h-12 text-base font-medium"
                        />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
                        <select
                            value={year}
                            onChange={e => setYear(e.target.value)}
                            className="input-premium h-12 min-w-[120px] font-bold text-gray-700 bg-white"
                        >
                            <option value="">Viti</option>
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                        <select
                            value={month}
                            onChange={e => setMonth(e.target.value)}
                            className="input-premium h-12 min-w-[140px] font-bold text-gray-700 bg-white"
                        >
                            {months.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                        <button
                            onClick={toggleSelectionMode}
                            className={`h-12 px-6 rounded-2xl text-sm font-bold transition-all flex items-center gap-2 ${selectionMode
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                : 'bg-white text-gray-600 border border-gray-100 hover:bg-gray-50'
                                }`}
                        >
                            {selectionMode ? <CheckSquare size={18} /> : null}
                            {selectionMode ? 'Anulo' : 'Selekto'}
                        </button>
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
                                        className={`w-full flex flex-col sm:flex-row sm:items-center justify-between px-8 py-6 text-left transition-all ${isExpanded ? 'bg-gray-50/50' : 'hover:bg-gray-50/30'
                                            }`}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-2 h-12 bg-blue-600 rounded-full group-hover/card:scale-y-110 transition-transform duration-300"></div>
                                            <div>
                                                <span className="text-lg font-black text-gray-900 group-hover/card:text-blue-600 transition-colors uppercase tracking-wide">{clientName}</span>
                                                <div className="flex items-center gap-2 text-gray-400 mt-1">
                                                    <span className="text-xs font-bold bg-white px-2 py-0.5 rounded-lg border border-gray-100">{group.invoices.length} fatura</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-6 mt-4 sm:mt-0">
                                            <div className="text-right">
                                                <div className="text-sm font-bold text-gray-400 uppercase tracking-widest">Gjithsej</div>
                                                <div className="text-xl font-black text-blue-600">{group.total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</div>
                                            </div>
                                            <div className={`p-2 rounded-xl bg-white border border-gray-100 text-gray-400 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                                                <Plus size={20} className={isExpanded ? 'rotate-45' : ''} />
                                            </div>
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
                                            {group.invoices.map((inv: any) => (
                                                <div
                                                    key={inv.id}
                                                    onClick={() => selectionMode && toggleSelect(inv.id)}
                                                    className={`relative p-4 rounded-2xl flex flex-col sm:grid sm:grid-cols-12 gap-4 items-center transition-all duration-300 ${selectionMode ? 'cursor-pointer' : ''
                                                        } ${selectionMode && selectedIds.has(inv.id)
                                                            ? 'bg-blue-50 border-blue-200'
                                                            : 'bg-white border border-gray-50 hover:border-blue-100 hover:shadow-md hover:shadow-blue-500/5'
                                                        }`}
                                                >
                                                    <div className="col-span-3 w-full">
                                                        <div className="flex items-center gap-3">
                                                            {selectionMode && (
                                                                <div className={`w-6 h-6 shrink-0 rounded-lg border-2 flex items-center justify-center transition-all ${selectedIds.has(inv.id)
                                                                    ? 'bg-blue-600 border-blue-600 shadow-lg shadow-blue-500/30'
                                                                    : 'border-gray-200 bg-white'
                                                                    }`}>
                                                                    {selectedIds.has(inv.id) && <CheckSquare size={14} className="text-white" />}
                                                                </div>
                                                            )}
                                                            <div className="min-w-0">
                                                                <div className="sm:hidden text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Numri & Data</div>
                                                                <div className="font-black text-gray-900 leading-none truncate">{inv.invoice_number}</div>
                                                                <div className="text-[11px] font-bold text-gray-400 mt-1.5 uppercase">{new Date(inv.date).toLocaleDateString('sq-AL')}</div>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div className="col-span-2 w-full">
                                                        <div className="sm:hidden text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Statusi</div>
                                                        {showStatus ? (
                                                            inv.status === 'paid' ? (
                                                                <span className="status-badge-paid w-fit">
                                                                    <CheckCircle2 size={12} /> E PAGUAR
                                                                </span>
                                                            ) : (
                                                                <span className="status-badge-unpaid w-fit">
                                                                    <XCircle size={12} /> E PAPAGUAR
                                                                </span>
                                                            )
                                                        ) : <div className="h-6" />}
                                                    </div>

                                                    <div className="col-span-2 w-full sm:text-right">
                                                        <div className="sm:hidden text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Shuma</div>
                                                        <div className="text-lg sm:text-base font-black text-gray-900">{parseFloat(inv.total).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</div>
                                                    </div>

                                                    <div className="col-span-5 w-full flex flex-wrap items-center justify-start sm:justify-end gap-2 pt-4 sm:pt-0 border-t sm:border-t-0 border-gray-50">
                                                        {!selectionMode && (
                                                            <>
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleDownloadPdf(inv.id); }}
                                                                    className="flex-1 sm:flex-none p-3 sm:p-2 bg-gray-50 sm:bg-transparent text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all flex items-center justify-center gap-2"
                                                                    title="PDF"
                                                                >
                                                                    <Download size={18} />
                                                                    <span className="sm:hidden font-bold text-xs uppercase">PDF</span>
                                                                </button>
                                                                <Link to={`/invoices/edit/${inv.id}`} onClick={(e) => e.stopPropagation()} className="flex-1 sm:flex-none">
                                                                    <button className="w-full p-3 sm:p-2 bg-blue-50 sm:bg-transparent text-blue-600 hover:text-blue-700 hover:bg-blue-100 rounded-xl transition-all flex items-center justify-center gap-2" title="Ndrysho">
                                                                        <Plus size={18} className="rotate-45" />
                                                                        <span className="sm:hidden font-bold text-xs uppercase">Edit</span>
                                                                    </button>
                                                                </Link>
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleClone(inv.id); }}
                                                                    className="flex-1 sm:flex-none p-3 sm:p-2 bg-amber-50 sm:bg-transparent text-amber-600 hover:text-amber-700 hover:bg-amber-100 rounded-xl transition-all flex items-center justify-center gap-2"
                                                                    title="Klono"
                                                                >
                                                                    <Copy size={18} />
                                                                    <span className="sm:hidden font-bold text-xs uppercase">Klon</span>
                                                                </button>
                                                                {showStatus && (
                                                                    <button
                                                                        onClick={(e) => { e.stopPropagation(); handleToggleStatus(inv.id, inv.status); }}
                                                                        className={`flex-1 sm:flex-none p-3 sm:p-2 bg-emerald-50 sm:bg-transparent ${inv.status === 'paid' ? 'text-emerald-600' : 'text-emerald-500'} hover:bg-emerald-100 rounded-xl transition-all flex items-center justify-center gap-2`}
                                                                        title="Ndrysho Statusin"
                                                                    >
                                                                        <CheckCircle2 size={18} />
                                                                        <span className="sm:hidden font-bold text-xs uppercase">Pagaj</span>
                                                                    </button>
                                                                )}
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleDelete(inv.id); }}
                                                                    className="flex-1 sm:flex-none p-3 sm:p-2 bg-rose-50 sm:bg-transparent text-rose-600 hover:text-rose-700 hover:bg-rose-100 rounded-xl transition-all flex items-center justify-center gap-2"
                                                                    title="Fshi"
                                                                >
                                                                    <Trash2 size={18} />
                                                                    <span className="sm:hidden font-bold text-xs uppercase">Fshi</span>
                                                                </button>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
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
