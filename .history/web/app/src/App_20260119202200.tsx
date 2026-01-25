import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import {
    LayoutDashboard,
    FileText,
    Users,
    Settings,
    Briefcase,
    Menu,
    X,
    Bell,
    Search,
    Plus,
    TrendingUp,
    Calendar,
    Clock,
    Shield
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import InvoicesPage from './pages/Invoices'
import OffersPage from './pages/Offers'
import ClientsPage from './pages/Clients'
import SettingsPage from './pages/Settings'

// Dashboard Component
const Dashboard = () => {
    const [stats, setStats] = useState<any>({ total_invoices: 0, total_revenue: 0, total_clients: 0 })
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('/api/dashboard/stats')
                const data = await response.json()
                setStats(data)
            } catch (error) {
                console.error('Error fetching stats:', error)
            } finally {
                setLoading(false)
            }
        }
        fetchStats()
    }, [])

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
            <h1 className="text-2xl font-bold mb-8 tracking-tight">Përmbledhja</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-shadow"
                >
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">Total Fatura</p>
                    <p className="text-4xl font-bold mt-4 tracking-tight">{loading ? '...' : stats.total_invoices}</p>
                    <div className="mt-4 flex items-center gap-1 text-green-500 text-xs font-bold">
                        <span>↑ 12%</span>
                        <span className="text-gray-400 font-medium">nga muaji i kaluar</span>
                    </div>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-shadow"
                >
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">Të hyrat Totale</p>
                    <p className="text-4xl font-bold mt-4 text-blue-600 tracking-tight">
                        {loading ? '...' : stats.total_revenue.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                    </p>
                    <div className="mt-4 flex items-center gap-1 text-green-500 text-xs font-bold">
                        <span>↑ 8.4%</span>
                        <span className="text-gray-400 font-medium">krahasuar me vitin 2024</span>
                    </div>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-shadow"
                >
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">Klientë Aktivë</p>
                    <p className="text-4xl font-bold mt-4 tracking-tight">{loading ? '...' : stats.total_clients}</p>
                    <div className="mt-4 flex items-center gap-1 text-blue-500 text-xs font-bold">
                        <span>Mbi 200 total</span>
                    </div>
                </motion.div>
            </div>

            <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="font-bold text-gray-900 mb-4">Aktivitetet e Fundit</h3>
                    <div className="space-y-4">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-xl transition-colors cursor-pointer group">
                                <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                    <FileText size={18} />
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm font-bold text-gray-900">Fatura #1024 u krijua</p>
                                    <p className="text-xs text-gray-500">Para 2 orëve • Klienti: Auto Pjesë Filani</p>
                                </div>
                                <span className="text-xs font-medium text-gray-400">22.01.2026</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                    <h3 className="font-bold text-gray-900 mb-4">Statistikat e Shitjeve</h3>
                    <div className="h-64 flex flex-col items-center justify-center">
                        <div className="flex items-end gap-6 h-40">
                            <motion.div initial={{ height: 0 }} animate={{ height: '100%' }} className="w-10 bg-blue-600 rounded-t-xl" title="Janar"></motion.div>
                            <motion.div initial={{ height: 0 }} animate={{ height: '60%' }} transition={{ delay: 0.1 }} className="w-10 bg-blue-400 rounded-t-xl" title="Shkurt"></motion.div>
                            <motion.div initial={{ height: 0 }} animate={{ height: '85%' }} transition={{ delay: 0.2 }} className="w-10 bg-blue-300 rounded-t-xl" title="Mars"></motion.div>
                            <motion.div initial={{ height: 0 }} animate={{ height: '45%' }} transition={{ delay: 0.3 }} className="w-10 bg-blue-200 rounded-t-xl" title="Prill"></motion.div>
                        </div>
                        <div className="mt-4 flex gap-6 text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                            <span>Jan</span>
                            <span>Shk</span>
                            <span>Mar</span>
                            <span>Pri</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

const SidebarItem = ({ icon: Icon, label, href, active }: any) => (
    <Link to={href}>
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${active ? 'bg-blue-50 text-blue-600 font-semibold shadow-sm' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
            }`}>
            <Icon size={20} />
            <span className="text-sm">{label}</span>
        </div>
    </Link>
)

const Layout = ({ children }: { children: React.ReactNode }) => {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const location = useLocation()

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
        { icon: FileText, label: 'Faturat', href: '/invoices' },
        { icon: Briefcase, label: 'Ofertat', href: '/offers' },
        { icon: Users, label: 'Klientët', href: '/clients' },
        { icon: Settings, label: 'Cilësimet', href: '/settings' },
    ]

    return (
        <div className="min-h-screen bg-[#F8FAFC] flex text-slate-900 selection:bg-blue-100 selection:text-blue-700">
            {/* Sidebar - Desktop */}
            <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-slate-200/60 p-5 sticky top-0 h-screen">
                <div className="flex items-center gap-3 px-2 mb-10 py-2">
                    <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white font-black text-xl shadow-lg shadow-blue-200">H</div>
                    <span className="text-xl font-bold tracking-tight text-slate-800">Holkos</span>
                </div>

                <nav className="flex-1 space-y-1.5">
                    {navItems.map((item) => (
                        <SidebarItem
                            key={item.href}
                            {...item}
                            active={location.pathname === item.href}
                        />
                    ))}
                </nav>

                <div className="mt-auto p-4 bg-slate-50 rounded-2xl border border-slate-100">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Versioni Web</p>
                    <div className="flex items-center justify-between">
                        <p className="text-sm font-bold text-slate-700">v1.0.0</p>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    </div>
                </div>
            </aside>

            {/* Mobile Sidebar */}
            <AnimatePresence>
                {sidebarOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSidebarOpen(false)}
                            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden"
                        />
                        <motion.aside
                            initial={{ x: -280 }}
                            animate={{ x: 0 }}
                            exit={{ x: -280 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed inset-y-0 left-0 w-72 bg-white z-50 p-6 shadow-2xl lg:hidden flex flex-col"
                        >
                            <div className="flex items-center justify-between mb-10">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white font-black shadow-lg shadow-blue-200">H</div>
                                    <span className="text-xl font-bold tracking-tight">Holkos</span>
                                </div>
                                <button onClick={() => setSidebarOpen(false)} className="p-2 text-slate-400 hover:bg-slate-50 rounded-xl"><X size={20} /></button>
                            </div>
                            <nav className="space-y-1.5 flex-1">
                                {navItems.map((item) => (
                                    <SidebarItem
                                        key={item.href}
                                        {...item}
                                        active={location.pathname === item.href}
                                    />
                                ))}
                            </nav>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <main className="flex-1 flex flex-col min-w-0">
                <header className="h-20 bg-white/70 backdrop-blur-xl border-b border-slate-200/60 flex items-center justify-between px-6 lg:px-10 sticky top-0 z-30">
                    <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-2.5 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors">
                        <Menu size={22} />
                    </button>

                    <div className="hidden lg:flex items-center relative max-w-md w-full">
                        <Search className="absolute left-4 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Kërko fatura, klientë..."
                            className="w-full bg-slate-100/50 border-none rounded-2xl py-2.5 pl-12 pr-4 text-sm focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all placeholder:text-slate-400"
                        />
                    </div>

                    <div className="flex items-center gap-3 md:gap-5">
                        <button className="p-2.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 rounded-xl relative transition-all">
                            <Bell size={20} />
                            <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-blue-600 rounded-full ring-2 ring-white"></span>
                        </button>
                        <div className="h-6 w-[1px] bg-slate-200 mx-1"></div>
                        <button className="flex items-center gap-3 p-1.5 pl-1.5 pr-4 hover:bg-slate-100 rounded-2xl transition-all group">
                            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 text-white flex items-center justify-center font-bold shadow-md shadow-blue-100 group-hover:scale-105 transition-transform">BH</div>
                            <div className="text-left hidden sm:block">
                                <p className="text-xs font-bold text-slate-800 leading-tight">Bleon H.</p>
                                <p className="text-[10px] text-slate-400 font-medium">Administrator</p>
                            </div>
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-auto bg-[#F8FAFC]">
                    <motion.div
                        key={location.pathname}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="h-full"
                    >
                        {children}
                    </motion.div>
                </div>
            </main>
        </div>
    )
}

import InvoiceForm from './pages/InvoiceForm'

function App() {
    return (
        <Router>
            <Layout>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/invoices" element={<InvoicesPage />} />
                    <Route path="/invoices/new" element={<InvoiceForm />} />
                    <Route path="/invoices/edit/:id" element={<InvoiceForm />} />
                    <Route path="/offers" element={<OffersPage />} />
                    <Route path="/offers/new" element={<InvoiceForm />} /> {/* Using InvoiceForm as template for now */}
                    <Route path="/offers/edit/:id" element={<InvoiceForm />} />
                    <Route path="/clients" element={<ClientsPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                </Routes>
            </Layout>
        </Router>
    )
}

export default App
