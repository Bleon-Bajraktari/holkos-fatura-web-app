import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Download, Trash2, ArrowLeft, RefreshCw, X, ChevronDown, FileText, Edit2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { ContractService, openPdf } from '../services/api'
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

const ContractsPage = () => {
    const navigate = useNavigate()
    const toast = useToast()
    const [contracts, setContracts] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [confirmDelete, setConfirmDelete] = useState<{ open: boolean; id?: number }>({ open: false })
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
            toast.error('Gabim gjatë hapjes së PDF: ' + ((e as any)?.response?.data?.detail || (e as Error)?.message))
        }
    }

    const handleDelete = async (id: number) => {
        try {
            await ContractService.delete(id)
            toast.success('Kontrata u fshi')
            loadContracts()
        } catch (e) {
            toast.error('Gabim gjatë fshirjes: ' + ((e as any)?.response?.data?.detail || (e as Error)?.message))
        }
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
                                    Lista e <span className="text-primary">Kontratave</span>
                                </h1>
                                <p className="text-[11px] text-muted-foreground font-medium mt-0.5 hidden sm:block">
                                    Kontratat e punës për kohë të pacaktuar
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button onClick={loadContracts} title="Rifresko" className="btn-icon shrink-0">
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                            </button>
                            <Link to="/contracts/new" className="hidden sm:block">
                                <button className="btn-primary flex items-center gap-2 px-4 py-2.5 text-sm">
                                    <Plus size={15} /> Kontratë e Re
                                </button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-2 sm:px-6 mt-3 sm:mt-8">
                {/* Search and Filters - si Faturat / Ofertat */}
                {/* Search + filter chips */}
                <div className="search-bar mb-3">
                    <Search className="text-muted-foreground shrink-0 ml-1" size={16} />
                    <input
                        type="text"
                        placeholder="Kërko sipas emrit, numrit personal..."
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

                {/* Year/Month chips */}
                <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1 mb-3">
                    {years.map(y => (
                        <button key={y} onClick={() => setYear(y)} className={`filter-chip shrink-0 ${year === y ? 'active' : ''}`}>{y}</button>
                    ))}
                    {years.length > 0 && <div className="w-px h-4 bg-border shrink-0 mx-1" />}
                    {months.slice(1).map(m => (
                        <button key={m} onClick={() => setMonth(month === m ? 'Të gjithë' : m)} className={`filter-chip shrink-0 ${month === m ? 'active' : ''}`}>{m}</button>
                    ))}
                </div>

                {/* Date range (hidden by default — keep as compact row) */}
                <div className="flex flex-wrap items-center gap-2 mb-3">
                    <div className="relative flex-1 min-w-[120px]">
                        <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input-base text-sm" placeholder="Nga data" />
                        {dateFrom && (
                            <button onClick={() => setDateFrom('')} className="absolute right-2 top-1/2 -translate-y-1/2"><X size={12} className="text-muted-foreground" /></button>
                        )}
                    </div>
                    <div className="relative flex-1 min-w-[120px]">
                        <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input-base text-sm" placeholder="Deri më" />
                        {dateTo && (
                            <button onClick={() => setDateTo('')} className="absolute right-2 top-1/2 -translate-y-1/2"><X size={12} className="text-muted-foreground" /></button>
                        )}
                    </div>
                    {(dateFrom || dateTo) && (
                        <button
                            type="button"
                            onClick={handleReset}
                            className="btn-secondary text-xs px-3 py-2"
                        >
                            Reset
                        </button>
                    )}
                </div>

                {/* Content Section */}
                <div className="space-y-3">
                    {loading ? (
                        <SkeletonList count={4} />
                    ) : personList.length === 0 ? (
                        <div className="card-base p-16 text-center">
                            <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <FileText size={28} className="text-muted-foreground/50" />
                            </div>
                            <h3 className="text-base font-bold text-foreground">Nuk u gjet asnjë kontratë</h3>
                            <p className="text-sm text-muted-foreground mt-1">Provo të ndryshosh filtrat.</p>
                            <Link to="/contracts/new">
                                <button className="btn-primary mt-4 px-5 py-2.5 text-sm flex items-center gap-2 mx-auto">
                                    <Plus size={15} /> Krijo Kontratë
                                </button>
                            </Link>
                        </div>
                    ) : (
                        personList.map((person) => {
                            const key = `${person.name}|${person.personalNumber}`
                            const isExpanded = expandedClients.has(key)
                            const grad = avatarGradient(person.name)
                            const sortedContracts = [...person.contracts].sort((a: any, b: any) => {
                                const da = a.contract_start_date || a.contract_date || ''
                                const db = b.contract_start_date || b.contract_date || ''
                                return db.localeCompare(da)
                            })
                            return (
                                <div key={key} className="card-base overflow-hidden">
                                    <button
                                        onClick={() => toggleClient(key)}
                                        className={`w-full flex items-center justify-between px-4 py-3.5 text-left transition-all ${isExpanded ? 'bg-muted/40 border-b border-border' : 'hover:bg-muted/30'}`}
                                    >
                                        <div className="flex items-center gap-3 min-w-0 flex-1">
                                            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center shrink-0 shadow-sm`}>
                                                <span className="text-[11px] font-black text-white">{initials(person.name)}</span>
                                            </div>
                                            <div className="min-w-0">
                                                <span className="text-sm font-black text-foreground uppercase tracking-wide block truncate">{person.name}</span>
                                                <div className="flex items-center gap-2 mt-0.5">
                                                    <span className="text-[10px] font-bold text-muted-foreground">{person.contracts.length} kontratë</span>
                                                    <span className="text-[10px] text-muted-foreground/50">·</span>
                                                    <span className="text-[10px] font-bold text-muted-foreground mono">NP: {person.personalNumber}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <ChevronDown size={16} className={`text-muted-foreground transition-transform duration-300 shrink-0 ${isExpanded ? 'rotate-180' : ''}`} />
                                    </button>

                                    <AnimatePresence initial={false}>
                                        {isExpanded && (
                                            <motion.div
                                                initial={{ height: 0 }}
                                                animate={{ height: 'auto' }}
                                                exit={{ height: 0 }}
                                                transition={{ duration: 0.25 }}
                                                className="overflow-hidden"
                                            >
                                                <div className="p-2 space-y-1.5">
                                                    {sortedContracts.map((c: any) => {
                                                        const isRowExpanded = expandedContractId === c.id
                                                        return (
                                                            <div key={c.id} className="rounded-xl border border-border bg-background hover:bg-muted/30 transition-all overflow-hidden">
                                                                <div
                                                                    onClick={() => toggleContractActions(c.id)}
                                                                    className="flex items-center gap-3 px-3 py-3 cursor-pointer"
                                                                >
                                                                    <div className="flex-1 min-w-0">
                                                                        <div className="text-sm font-black text-foreground mono">{formatDate(c.contract_date || c.contract_start_date)}</div>
                                                                        <div className="text-[11px] text-muted-foreground font-medium mono mt-0.5">
                                                                            Paga bruto: {Number(c.gross_salary)?.toLocaleString('sq-AL')} €
                                                                        </div>
                                                                    </div>
                                                                    <ChevronDown size={14} className={`text-muted-foreground transition-transform duration-200 shrink-0 ${isRowExpanded ? 'rotate-180' : ''}`} />
                                                                </div>

                                                                <AnimatePresence>
                                                                    {isRowExpanded && (
                                                                        <motion.div
                                                                            initial={{ height: 0, opacity: 0 }}
                                                                            animate={{ height: 'auto', opacity: 1 }}
                                                                            exit={{ height: 0, opacity: 0 }}
                                                                            transition={{ duration: 0.18 }}
                                                                            className="border-t border-border/60 overflow-hidden"
                                                                        >
                                                                            <div className="px-3 pt-2.5 pb-3 space-y-2">
                                                                                <motion.button
                                                                                    whileTap={{ scale: 0.97 }}
                                                                                    onClick={() => navigate(`/contracts/edit/${c.id}`)}
                                                                                    className="w-full h-8 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm shadow-violet-500/25"
                                                                                >
                                                                                    <Edit2 size={12} />
                                                                                    Ndrysho Kontratën
                                                                                </motion.button>
                                                                                <div className="grid grid-cols-2 gap-1.5">
                                                                                    <motion.button
                                                                                        whileTap={{ scale: 0.94 }}
                                                                                        onClick={() => handleDownloadPdf(c.id)}
                                                                                        className="flex flex-col items-center gap-0.5 py-1.5 rounded-lg bg-indigo-500/10 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 transition-colors active:bg-indigo-500/20"
                                                                                    >
                                                                                        <Download size={13} />
                                                                                        <span className="text-[10px] font-black tracking-wide">PDF</span>
                                                                                    </motion.button>
                                                                                    <motion.button
                                                                                        whileTap={{ scale: 0.94 }}
                                                                                        onClick={() => setConfirmDelete({ open: true, id: c.id })}
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
                        })
                    )}
                </div>
            </div>

            {/* Mobile FAB — Kontratë e Re */}
            <Link
                to="/contracts/new"
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

            <ConfirmDialog
                isOpen={confirmDelete.open}
                title="Fshi kontratën"
                message="A jeni të sigurt se doni të fshini këtë kontratë? Ky veprim është i pakthyeshëm."
                confirmLabel="Fshi"
                onConfirm={() => {
                    if (confirmDelete.id != null) handleDelete(confirmDelete.id)
                    setConfirmDelete({ open: false })
                }}
                onCancel={() => setConfirmDelete({ open: false })}
            />
        </div>
    )
}

export default ContractsPage
