import { useState } from 'react'
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
    Plus
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

// Placeholder components for pages
const Dashboard = () => (
    <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <p className="text-sm font-medium text-gray-500">Total Fatura</p>
                <p className="text-3xl font-bold mt-2">124</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <p className="text-sm font-medium text-gray-500">Të hyrat Totale</p>
                <p className="text-3xl font-bold mt-2 text-blue-600">45,230.00 €</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <p className="text-sm font-medium text-gray-500">Klientë Aktivë</p>
                <p className="text-3xl font-bold mt-2">56</p>
            </div>
        </div>
    </div>
)

const SidebarItem = ({ icon: Icon, label, href, active }: any) => (
    <Link to={href}>
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${active ? 'bg-blue-50 text-blue-600 font-medium shadow-sm' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
            }`}>
            <Icon size={20} />
            <span>{label}</span>
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
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar - Desktop */}
            <aside className="hidden md:flex flex-col w-64 bg-white border-r border-gray-100 p-4 sticky top-0 h-screen">
                <div className="flex items-center gap-2 px-4 mb-8 py-2">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">H</div>
                    <span className="text-xl font-bold tracking-tight">Holkos Fatura</span>
                </div>

                <nav className="flex-1 space-y-1">
                    {navItems.map((item) => (
                        <SidebarItem
                            key={item.href}
                            {...item}
                            active={location.pathname === item.href}
                        />
                    ))}
                </nav>

                <div className="mt-auto p-4 bg-gray-50 rounded-2xl">
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Versioni Web</p>
                    <p className="text-sm font-bold text-gray-900">v1.0.0</p>
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
                            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
                        />
                        <motion.aside
                            initial={{ x: -280 }}
                            animate={{ x: 0 }}
                            exit={{ x: -280 }}
                            className="fixed inset-y-0 left-0 w-64 bg-white z-50 p-4 shadow-xl md:hidden"
                        >
                            <div className="flex items-center justify-between mb-8 px-2">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">H</div>
                                    <span className="text-xl font-bold">Holkos</span>
                                </div>
                                <button onClick={() => setSidebarOpen(false)} className="p-2 text-gray-500"><X size={20} /></button>
                            </div>
                            <nav className="space-y-1">
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
                <header className="h-16 bg-white/80 backdrop-blur-md border-b border-gray-100 flex items-center justify-between px-4 md:px-8 sticky top-0 z-30">
                    <button onClick={() => setSidebarOpen(true)} className="md:hidden p-2 text-gray-500 hover:bg-gray-50 rounded-lg">
                        <Menu size={20} />
                    </button>

                    <div className="hidden md:flex items-center relative max-w-md w-full">
                        <Search className="absolute left-3 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Kërko fatura, klientë..."
                            className="w-full bg-gray-50 border-none rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                        />
                    </div>

                    <div className="flex items-center gap-2 md:gap-4">
                        <button className="p-2 text-gray-500 hover:bg-gray-50 rounded-xl relative">
                            <Bell size={20} />
                            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
                        </button>
                        <div className="h-8 w-[1px] bg-gray-100 mx-2"></div>
                        <button className="flex items-center gap-2 p-1 pr-3 hover:bg-gray-50 rounded-xl transition-all">
                            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">BH</div>
                            <span className="text-sm font-medium hidden sm:inline">Bleon H.</span>
                        </button>
                        <button className="hidden sm:flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-blue-700 shadow-md shadow-blue-200 transition-all">
                            <Plus size={18} />
                            <span>Krijo Faturë</span>
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-auto">
                    {children}
                </div>
            </main>
        </div>
    )
}

import InvoicesPage from './pages/Invoices'
import OffersPage from './pages/Offers'
import ClientsPage from './pages/Clients'

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
            <h1 className="text-2xl font-bold mb-8">Përmbledhja</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white p-6 rounded-22xl shadow-sm border border-gray-100 flex flex-col justify-between"
                >
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">Total Fatura</p>
                    <p className="text-4xl font-bold mt-4">{loading ? '...' : stats.total_invoices}</p>
                    <div className="mt-4 flex items-center gap-1 text-green-500 text-xs font-bold">
                        <span>↑ 12%</span>
                        <span className="text-gray-400 font-medium">nga muaji i kaluar</span>
                    </div>
                </motion.div>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white p-6 rounded-22xl shadow-sm border border-gray-100 flex flex-col justify-between"
                >
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">Të hyrat Totale</p>
                    <p className="text-4xl font-bold mt-4 text-blue-600">
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
                    className="bg-white p-6 rounded-22xl shadow-sm border border-gray-100 flex flex-col justify-between"
                >
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">Klientë Aktivë</p>
                    <p className="text-4xl font-bold mt-4">{loading ? '...' : stats.total_clients}</p>
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
                            <div key={i} className="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-xl transition-colors">
                                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500">
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
                    <h3 className="font-bold text-gray-900 mb-4">Shitjet sipas Kategorisë</h3>
                    <div className="h-64 flex items-center justify-center text-gray-300">
                        {/* Imaginary Chart */}
                        <div className="flex flex-col items-center gap-2">
                            <div className="flex items-end gap-4 h-32">
                                <div className="w-8 bg-blue-500 rounded-t-lg h-full"></div>
                                <div className="w-8 bg-blue-400 rounded-t-lg h-2/3"></div>
                                <div className="w-8 bg-blue-300 rounded-t-lg h-4/5"></div>
                                <div className="w-8 bg-blue-200 rounded-t-lg h-1/2"></div>
                            </div>
                            <span className="text-xs font-medium">Grafiku i shitjeve (Bashkëpunimi vjetor)</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

function App() {
    return (
        <Router>
            <Layout>
                <div className="animate-in fade-in duration-500">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/invoices" element={<InvoicesPage />} />
                        <Route path="/offers" element={<OffersPage />} />
                        <Route path="/clients" element={<ClientsPage />} />
                        <Route path="/settings" element={<div className="p-6">Cilësimet</div>} />
                    </Routes>
                </div>
            </Layout>
        </Router>
    )
}

export default App
