import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, ArrowLeft, RefreshCw, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { ContractService, openPdf } from '../services/api'

const months = [
    'Të gjithë', 'Janar', 'Shkurt', 'Mars', 'Prill', 'Maj', 'Qershor',
    'Korrik', 'Gusht', 'Shtator', 'Tetor', 'Nëntor', 'Dhjetor'
]

const ContractsPage = () => {
    const navigate = useNavigate()
    const [contracts, setContracts] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [year, setYear] = useState('')
    const [month, setMonth] = useState('Të gjithë')
    const [years, setYears] = useState<string[]>([])
    const [yearsLoaded, setYearsLoaded] = useState(false)
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set())
    const [expandedContractId, setExpandedContractId] = useState<number | null>(null)

    const loadContracts = () => {
        setLoading(true)
        const params: Record<string, string> = {}
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
        ContractService.getAll(Object.keys(params).length ? params : undefined)
            .then(data => setContracts(Array.isArray(data) ? data : []))
            .catch(err => {
                console.error('Error loading contracts:', err)
                setContracts([])
            })
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedSearch(search), 400)
        return () => clearTimeout(timer)
    }, [search])

    useEffect(() => {
        ContractService.getYears().then(data => {
            const yrs = data.years || []
            setYears(yrs)
            if (yrs.length) {
                const latest = String(Math.max(...yrs.map((y: string) => parseInt(y, 10))))
                setYear(latest)
            }
            setYearsLoaded(true)
        }).catch(() => { setYears([]); setYearsLoaded(true) })
    }, [])

    useEffect(() => {
        if (!yearsLoaded) return
        loadContracts()
    }, [yearsLoaded, debouncedSearch, year, month, dateFrom, dateTo])

    const handleReset = () => {
        setSearch('')
        setYear(years.length ? String(Math.max(...years.map(y => parseInt(y, 10)))) : '')
        setMonth('Të gjithë')
        setDateFrom('')
        setDateTo('')
    }

    const formatDate = (d: string | null) => {
        if (!d) return '–'
        try {
            return new Date(d).toLocaleDateString('sq-AL', { day: '2-digit', month: '2-digit', year: 'numeric' })
        } catch {
            return d
        }
    }

    const personKey = (c: any) => `${(c.employee_name || '').trim()}|${(c.personal_number || '').trim()}`
    const byPerson = contracts.reduce<Record<string, { name: string; personalNumber: string; residence?: string; contracts: any[] }>>((acc, c) => {
        const key = personKey(c)
        if (!acc[key]) {
            acc[key] = {
                name: (c.employee_name || '').trim() || '–',
                personalNumber: (c.personal_number || '').trim() || '–',
                residence: c.residence?.trim() || undefined,
                contracts: [],
            }
        }
        acc[key].contracts.push(c)
        return acc
    }, {})
    const personList = Object.values(byPerson).sort((a, b) => a.name.localeCompare(b.name, 'sq'))

    const toggleClient = (key: string) => {
        setExpandedClients(prev => {
            const next = new Set(prev)
            if (next.has(key)) next.delete(key)
            else next.add(key)
            return next
        })
    }

    const toggleContractActions = (id: number) => {
        setExpandedContractId(prev => (prev === id ? null : id))
    }

    const handleDownloadPdf = async (id: number) => {
        try {
            await openPdf(ContractService.getPdfPath(id))
        } catch (e) {
            alert('Gabim gjatë hapjes së PDF: ' + (e as any)?.response?.data?.detail || (e as Error)?.message)
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm('A jeni të sigurt që doni ta fshini këtë kontratë?')) return
        try {
            await ContractService.delete(id)
            loadContracts()
        } catch (e) {
            alert('Gabim gjatë fshirjes: ' + (e as any)?.response?.data?.detail || (e as Error)?.message)
        }
    }

    return (
        <div className="min-h-screen pb-12">
            {/* Header Section - si Faturat / Ofertat */}
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
                                <h1 className="text-lg sm:text-2xl font-black text-gray-900 tracking-tight leading-none sm:leading-normal">Lista e <span className="gradient-text">Kontratave</span></h1>
                                <p className="text-gray-500 text-[10px] sm:text-sm font-medium">Kontratat e punës për kohë të pacaktuar</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={loadContracts}
                                title="Rifresko"
                                className="p-2.5 bg-gray-50 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-300 active:scale-95 flex items-center justify-center shrink-0"
                            >
                                <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <Link to="/contracts/new" className="w-full sm:w-auto">
                                <button className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white px-8 py-2.5 sm:px-14 sm:py-3 rounded-xl sm:rounded-2xl font-bold text-xs sm:text-sm shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 w-full active:scale-95 transition-all">
                                    <Plus size={16} />
                                    <span>Krijo kontratë</span>
                                </button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-2 sm:px-6 mt-3 sm:mt-8">
                {/* Search and Filters - si Faturat / Ofertat */}
                <div className="glass p-2 sm:p-5 rounded-2xl sm:rounded-[2.5rem] mb-3 sm:mb-8 shadow-xl shadow-blue-500/5 border-white/40">
                    <div className="flex flex-col gap-2 sm:gap-5">
                        <div className="flex items-center bg-gray-50/50 border border-gray-100/80 rounded-xl px-3 sm:px-5 h-10 sm:h-14 group focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 focus-within:bg-white transition-all shadow-inner">
                            <Search className="text-gray-400 group-focus-within:text-blue-500 transition-colors shrink-0" size={16} />
                            <input
                                type="text"
                                placeholder="Kërko sipas emrit, numrit personal ose vendbanimit..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="flex-1 bg-transparent border-none outline-none pl-2 sm:pl-4 text-xs sm:text-[16px] font-medium h-full w-full"
                            />
                        </div>

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
                                            type="button"
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
                                            type="button"
                                            onClick={() => setDateTo('')}
                                            className="absolute right-1 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                                        >
                                            <X size={12} className="text-gray-400" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="col-span-12 sm:col-span-6 lg:col-span-2 flex items-end">
                                <button
                                    type="button"
                                    onClick={handleReset}
                                    className="h-9 sm:h-11 w-full rounded-lg sm:rounded-xl text-[9px] sm:text-[10px] font-black bg-white/50 border border-gray-100 text-gray-600 hover:bg-gray-100 transition-all flex items-center justify-center gap-1 sm:gap-2 shadow-sm"
                                >
                                    RESET
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
                            <p className="font-bold animate-pulse">Duke ngarkuar kontratat...</p>
                        </div>
                    ) : personList.length === 0 ? (
                        <div className="bg-white rounded-[2rem] p-16 text-center shadow-sm border border-gray-100">
                            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Search size={32} className="text-gray-300" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">Nuk u gjet asnjë kontratë</h3>
                            <p className="text-gray-500 mt-2">Provo të ndryshosh filtrat ose kërkimin tuaj.</p>
                            <Link to="/contracts/new">
                                <button className="mt-4 text-blue-600 font-bold hover:underline">Krijo kontratë</button>
                            </Link>
                        </div>
                    ) : (
                        personList.map((person) => {
                            const key = `${person.name}|${person.personalNumber}`
                            const isExpanded = expandedClients.has(key)
                            const sortedContracts = [...person.contracts].sort((a: any, b: any) => {
                                const da = a.contract_start_date || a.contract_date || ''
                                const db = b.contract_start_date || b.contract_date || ''
                                return db.localeCompare(da)
                            })
                            return (
                                <div key={key} className="bg-white rounded-xl sm:rounded-2xl border border-gray-100/80 overflow-hidden group/card shadow-sm hover:shadow-md transition-all duration-300">
                                    <button
                                        onClick={() => toggleClient(key)}
                                        className={`w-full min-h-[4rem] sm:min-h-[4.5rem] flex items-center justify-between px-3 sm:px-5 py-2.5 text-left transition-all ${isExpanded ? 'bg-gray-50/50' : 'hover:bg-gray-50/30'}`}
                                    >
                                        <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
                                            <div className="w-1 self-stretch min-h-[1.5rem] bg-blue-600 rounded-full shrink-0"></div>
                                            <div className="flex flex-col gap-y-1 min-w-0">
                                                <span className="text-[13px] sm:text-sm font-black text-gray-900 uppercase tracking-wide leading-tight break-words">{person.name}</span>
                                                <div className="flex flex-wrap items-center gap-2 sm:gap-3 shrink-0">
                                                    <span className="text-[9px] sm:text-[10px] font-bold text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded-md border border-gray-100 uppercase">{person.contracts.length} kontratë</span>
                                                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">NP: {person.personalNumber}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={`p-1 rounded-lg bg-white border border-gray-100 text-gray-400 transition-transform duration-300 shrink-0 ${isExpanded ? 'rotate-180 bg-blue-50 text-blue-600' : ''}`}>
                                            <Plus size={12} className={isExpanded ? 'rotate-45' : ''} />
                                        </div>
                                    </button>

                                    {isExpanded && (
                                        <div className="px-4 sm:px-8 pb-8 space-y-4 pt-2">
                                            <div className="hidden sm:grid grid-cols-12 gap-4 px-4 py-2 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] border-b border-gray-50">
                                                <div className="col-span-4">Data</div>
                                                <div className="col-span-4 text-right">Paga (bruto)</div>
                                                <div className="col-span-4 text-right">Veprimet</div>
                                            </div>
                                            {sortedContracts.map((c: any) => {
                                                const isRowExpanded = expandedContractId === c.id
                                                return (
                                                    <div
                                                        key={c.id}
                                                        className="relative overflow-hidden transition-all duration-300 bg-white border border-gray-100/50 hover:border-blue-100/50 shadow-sm hover:shadow-md rounded-2xl"
                                                    >
                                                        <div
                                                            onClick={() => toggleContractActions(c.id)}
                                                            className="flex items-center justify-between sm:grid sm:grid-cols-12 sm:gap-4 gap-2 px-4 py-2.5 cursor-pointer"
                                                        >
                                                            <div className="flex items-center gap-3 min-w-0 sm:col-span-4">
                                                                <div className="min-w-0">
                                                                    <div className="font-bold text-gray-900 text-sm">{formatDate(c.contract_date || c.contract_start_date)}</div>
                                                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-tight sm:hidden">Paga: {Number(c.gross_salary)?.toLocaleString('sq-AL')} €</div>
                                                                </div>
                                                            </div>
                                                            <div className="hidden sm:block col-span-4 text-right">
                                                                <span className="text-sm font-black text-gray-900">{Number(c.gross_salary)?.toLocaleString('sq-AL')} €</span>
                                                            </div>
                                                            <div className="flex sm:justify-end col-span-2 sm:col-span-4 items-center justify-end">
                                                                <div className={`p-1.5 rounded-lg bg-gray-50 text-gray-400 transition-transform duration-300 shrink-0 ${isRowExpanded ? 'rotate-180 bg-blue-50 text-blue-600' : ''}`}>
                                                                    <Plus size={14} className={isRowExpanded ? 'rotate-45' : ''} />
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <AnimatePresence>
                                                            {isRowExpanded && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: 'auto', opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="border-t border-gray-50 bg-gray-50/30 overflow-hidden"
                                                                >
                                                                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-end gap-2">
                                                                        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                                                                            <button
                                                                                onClick={() => handleDownloadPdf(c.id)}
                                                                                className="flex-1 sm:flex-none h-9 px-4 bg-white border border-gray-200 text-gray-600 rounded-xl text-xs font-bold hover:bg-gray-50 transition-all flex items-center justify-center gap-2"
                                                                            >
                                                                                <Download size={16} /> PDF
                                                                            </button>
                                                                            <button
                                                                                onClick={() => navigate(`/contracts/edit/${c.id}`)}
                                                                                className="flex-1 sm:flex-none h-9 px-4 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20"
                                                                            >
                                                                                NDRYSHO
                                                                            </button>
                                                                            <button
                                                                                onClick={() => handleDelete(c.id)}
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
        </div>
    )
}

export default ContractsPage
