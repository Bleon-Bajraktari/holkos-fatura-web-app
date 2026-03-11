import { useState, useEffect, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate, Outlet } from 'react-router-dom'
import {
    LayoutDashboard,
    FileText,
    FileSignature,
    Users,
    Settings,
    Briefcase,
    Menu,
    X,
    Bell,
    Search,
    TrendingUp,
    Calendar,
    Clock,
    Shield,
    Layers,
    FilePlus,
    LogOut,
    Moon,
    Sun
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { CompanyService, DashboardService, SettingsService, API_BASE } from './services/api'
import InvoicesPage from './pages/Invoices'
import OffersPage from './pages/Offers'
import ClientsPage from './pages/Clients'
import ContractsPage from './pages/Contracts.tsx'
import ContractForm from './pages/ContractForm.tsx'
import SettingsPage from './pages/Settings'
import TemplatesPage from './pages/Templates'
import OfferForm from './pages/OfferForm'
import Login from './pages/Login'
import NetworkStatus from './components/NetworkStatus'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import { useActivityTracker } from './hooks/useActivityTracker'

// Dashboard Component
const Dashboard = () => {
    const [stats, setStats] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async (retries = 1) => {
            try {
                const data = await DashboardService.getStats()
                setStats(data)
                if (data) localStorage.setItem('dashboard_cache', JSON.stringify(data))
            } catch (error) {
                console.error('Error fetching stats:', error)
                if (retries > 0) {
                    await new Promise(r => setTimeout(r, 2500))
                    return fetchStats(retries - 1)
                }
                try {
                    const cached = localStorage.getItem('dashboard_cache')
                    if (cached) setStats(JSON.parse(cached))
                } catch (_) {}
            } finally {
                setLoading(false)
            }
        }
        fetchStats()
    }, [])

    if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Duke u ngarkuar...</div>

    const statCards = [
        { label: 'Totali i Faturave', value: stats?.total_invoices || 0, icon: <FileText size={20} />, color: 'bg-blue-500', trend: 'Gjithsej' },
        { label: 'Faturat këtë Muaj', value: stats?.month_invoices || 0, icon: <Calendar size={20} />, color: 'bg-purple-500', trend: 'Muaji aktual' },
        { label: 'Ardhura Totale', value: `${(stats?.total_revenue || 0).toLocaleString('sq-AL')} €`, icon: <TrendingUp size={20} />, color: 'bg-green-500', trend: stats?.growth > 0 ? `+${stats.growth}% këtë muaj` : `${stats?.growth || 0}% këtë muaj` },
        { label: 'TVSH e Grumbulluar', value: `${(stats?.total_vat || 0).toLocaleString('sq-AL')} €`, icon: <Shield size={20} />, color: 'bg-amber-500', trend: 'Totali TVSH' },
    ]

    const quickActions = [
        { label: 'Faturat', href: '/invoices', icon: <FileText size={18} />, color: 'text-blue-600 bg-blue-50' },
        { label: 'Ofertat', href: '/offers', icon: <Layers size={18} />, color: 'text-amber-600 bg-amber-50' },
        { label: 'Kontratat', href: '/contracts', icon: <FileSignature size={18} />, color: 'text-indigo-600 bg-indigo-50' },
        { label: 'Klientë', href: '/clients', icon: <Users size={18} />, color: 'text-emerald-600 bg-emerald-50' },
        { label: 'Cilësime', href: '/settings', icon: <Settings size={18} />, color: 'text-rose-600 bg-rose-50' },
    ]

    return (
        <div className="p-4 sm:p-6 md:p-10 max-w-7xl mx-auto w-full space-y-8">
            <header>
                <h1 className="text-3xl font-black text-foreground tracking-tight">Përmbledhja e Biznesit</h1>
                <p className="text-muted-foreground font-medium mt-1">Statistikat kryesore dhe aktiviteti i fundit.</p>
            </header>

            <div className="bg-card p-6 sm:p-8 rounded-[2rem] sm:rounded-[3rem] border border-border shadow-sm">
                <div className="flex items-center justify-between mb-5">
                    <h3 className="text-lg font-black text-foreground flex items-center gap-2">
                        <LayoutDashboard size={20} className="text-blue-500" />
                        Veprime të shpejta
                    </h3>

                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    {quickActions.map((action) => (
                        <Link key={action.href} to={action.href}>
                            <div className="flex items-center gap-3 px-3 py-3 rounded-2xl border border-border hover:border-primary/40 hover:shadow-sm transition-all bg-card">
                                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${action.color}`}>
                                    {action.icon}
                                </div>
                                <span className="text-xs font-bold text-foreground">{action.label}</span>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((card, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-card p-6 rounded-[2.5rem] border border-border shadow-sm hover:shadow-xl hover:shadow-primary/5 transition-all group"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className={`${card.color} w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-current/20 group-hover:scale-110 transition-transform`}>
                                {card.icon}
                            </div>
                        </div>
                        <h3 className="text-muted-foreground text-xs font-black uppercase tracking-widest mb-1">{card.label}</h3>
                        <p className="text-2xl font-black text-foreground leading-tight">{card.value}</p>
                        <div className="mt-4 flex items-center gap-1.5">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${String(stats?.growth).includes('+') || stats?.growth > 0 ? 'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-muted text-muted-foreground'}`}>
                                {card.trend}
                            </span>
                        </div>
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-card p-6 sm:p-8 rounded-[2rem] sm:rounded-[3rem] border border-border shadow-sm space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <h3 className="text-lg font-black text-foreground flex items-center gap-2">
                            <Clock size={20} className="text-blue-500" />
                            Faturat e Fundit
                        </h3>
                        <Link to="/invoices">
                            <button className="text-xs font-bold text-primary hover:text-primary/80 transition-colors uppercase tracking-widest">Shiko të Gjitha</button>
                        </Link>
                    </div>

                    <div className="space-y-4">
                        {stats?.recent_activity?.filter((act: any) => act.type === 'invoice')?.map((act: any, idx: number) => (
                            <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-3xl hover:bg-muted/50 transition-colors border border-transparent hover:border-border group">
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-2xl flex items-center justify-center ${act.type === 'invoice' ? 'bg-primary/10 text-primary' : 'bg-amber-50 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400'}`}>
                                        {act.type === 'invoice' ? <FileText size={18} /> : <Briefcase size={18} />}
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-foreground">{act.client}</p>
                                        <p className="text-xs text-muted-foreground font-medium">#{act.number} • {new Date(act.date).toLocaleDateString('sq-AL')}</p>
                                    </div>
                                </div>
                                <div className="text-left sm:text-right">
                                    <p className="text-sm font-black text-foreground">{act.amount.toLocaleString('sq-AL')} €</p>
                                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{act.type === 'invoice' ? 'Faturë' : 'Ofertë'}</p>
                                </div>
                            </div>
                        ))}
                        {(!stats?.recent_activity || stats.recent_activity.filter((act: any) => act.type === 'invoice').length === 0) && (
                            <p className="text-center py-10 text-muted-foreground text-sm italic font-medium">Nuk ka aktivitet të fundit.</p>
                        )}
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-card p-6 sm:p-8 rounded-[2rem] sm:rounded-[3rem] border border-border shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-black text-foreground flex items-center gap-2">
                                <Briefcase size={18} className="text-amber-500" />
                                Ofertat e Fundit
                            </h3>
                            <Link to="/offers" className="text-[10px] font-bold text-amber-600 dark:text-amber-300 uppercase tracking-widest">Shiko</Link>
                        </div>
                        <div className="space-y-3">
                            {stats?.recent_activity?.filter((act: any) => act.type === 'offer')?.map((act: any, idx: number) => (
                                <div key={idx} className="flex items-center justify-between gap-3 p-3 rounded-2xl border border-border">
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="w-8 h-8 rounded-xl bg-amber-50 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                                            <Briefcase size={14} />
                                        </div>
                                        <div className="min-w-0">
                                            <p className="text-xs font-bold text-foreground truncate">{act.client}</p>
                                            <p className="text-[10px] text-muted-foreground font-medium truncate">#{act.number}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs font-black text-foreground">{act.amount.toLocaleString('sq-AL')} €</p>
                                    </div>
                                </div>
                            ))}
                            {(!stats?.recent_activity || stats.recent_activity.filter((act: any) => act.type === 'offer').length === 0) && (
                                <p className="text-center py-6 text-muted-foreground text-xs italic font-medium">Nuk ka oferta të fundit.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

const ScrollToTop = () => {
    const location = useLocation()

    useEffect(() => {
        window.scrollTo({ top: 0, left: 0, behavior: 'instant' as ScrollBehavior })
    }, [location.pathname])

    return null
}

const SidebarItem = ({ icon: Icon, label, href, active }: any) => (
    <Link to={href}>
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${active ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold shadow-sm' : 'text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-700/50 hover:text-gray-900 dark:hover:text-slate-100'
            }`}>
            <Icon size={20} />
            <span className="text-sm">{label}</span>
        </div>
    </Link>
)

const Layout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const location = useLocation()
    const navigate = useNavigate()
    const [company, setCompany] = useState<any>(null)
    const [navbarCombined, setNavbarCombined] = useState(true)
    const prevPathRef = useRef(location.pathname)
    const { logout, refreshToken } = useAuth()
    const { isDark, toggleTheme } = useTheme()

    const handleLogout = () => {
        logout()
        navigate('/login', { replace: true })
    }
    useActivityTracker(true, logout, refreshToken)

    const navItemsCombined = [
        { icon: LayoutDashboard, label: 'Raporte', href: '/' },
        { icon: FileText, label: 'Faturat', href: '/invoices' },
        { icon: Layers, label: 'Ofertat', href: '/offers' },
        { icon: FileSignature, label: 'Kontratat', href: '/contracts' },
        { icon: Users, label: 'Klientë', href: '/clients' },
        { icon: Layers, label: 'Shabllona', href: '/templates' },
        { icon: Settings, label: 'Cilësime', href: '/settings' },
    ]
    const navItemsSplit = [
        { icon: LayoutDashboard, label: 'Raporte', href: '/' },
        { icon: FilePlus, label: 'Faturë e re', href: '/invoices/new' },
        { icon: FileText, label: 'Lista e faturave', href: '/invoices' },
        { icon: Briefcase, label: 'Ofertë e re', href: '/offers/new' },
        { icon: Layers, label: 'Lista e ofertave', href: '/offers' },
        { icon: FilePlus, label: 'Kontratë e re', href: '/contracts/new' },
        { icon: FileSignature, label: 'Lista e kontratave', href: '/contracts' },
        { icon: Users, label: 'Klientë', href: '/clients' },
        { icon: Layers, label: 'Shabllona', href: '/templates' },
        { icon: Settings, label: 'Cilësime', href: '/settings' },
    ]
    const navItems = navbarCombined ? navItemsCombined : navItemsSplit

    const isNavItemActive = (href: string) =>
        href === '/' ? location.pathname === '/' : (location.pathname === href || location.pathname.startsWith(href + '/'))

    useEffect(() => {
        if (sidebarOpen) {
            setSidebarOpen(false)
        }
    }, [location.pathname])

    useEffect(() => {
        // Shiko në cache së pari për shpejtësi (PWA)
        const cached = localStorage.getItem('company_cache')
        if (cached) {
            setCompany(JSON.parse(cached))
        }

        CompanyService.get()
            .then(data => {
                setCompany(data)
                localStorage.setItem('company_cache', JSON.stringify(data))
            })
            .catch(() => {
                if (!cached) setCompany(null)
            })
    }, [])

    useEffect(() => {
        SettingsService.getNavbarCombined()
            .then((data: { combined?: boolean }) => setNavbarCombined(data.combined !== false))
            .catch(() => setNavbarCombined(true))
    }, [])

    useEffect(() => {
        if (prevPathRef.current === '/settings' && location.pathname !== '/settings') {
            SettingsService.getNavbarCombined()
                .then((data: { combined?: boolean }) => setNavbarCombined(data.combined !== false))
                .catch(() => {})
        }
        prevPathRef.current = location.pathname
    }, [location.pathname])

    const logoUrl = company?.logo_path
        ? (API_BASE && API_BASE.startsWith('http')
            ? `${API_BASE.replace(/\/$/, '')}/${company.logo_path.replace(/^\/+/, '')}`
            : `/${company.logo_path.replace(/^\/+/, '')}`)
        : ''

    useEffect(() => {
        const version = Date.now()
        const updateLink = (rel: string, href: string) => {
            // Gjej të gjitha link-et me këtë rel (p.sh. apple-touch-icon mund të ketë sizes)
            const links = document.querySelectorAll(`link[rel="${rel}"], link[rel*="${rel}"]`)
            links.forEach(link => {
                (link as HTMLLinkElement).href = `${href}?v=${version}`
            })

            // Nëse nuk ka link, krijo një të ri
            if (links.length === 0) {
                const link = document.createElement('link')
                link.rel = rel
                link.href = `${href}?v=${version}`
                document.head.appendChild(link)
            }
        }

        // Përditëso favicon me logo-n e kompanisë nëse ekziston
        if (logoUrl) {
            updateLink('icon', logoUrl)
        }

        // Gjithmonë përditëso apple-touch-icon me endpoint-in e backend-it
        updateLink('apple-touch-icon', (API_BASE && API_BASE.startsWith('http') ? `${API_BASE}/apple-touch-icon.png` : '/apple-touch-icon.png'))
    }, [logoUrl])

    return (
        <div className="min-h-screen bg-background text-foreground flex selection:bg-blue-100 dark:selection:bg-blue-900 selection:text-blue-700 dark:selection:text-blue-200">
            {/* Sidebar - Desktop */}
            <aside className="hidden lg:flex flex-col w-64 bg-card border-r border-border p-5 sticky top-0 h-screen">
                <div className="flex items-center gap-3 px-2 mb-10 py-2">
                    {logoUrl ? (
                        <img
                            src={logoUrl}
                            alt="Holkos"
                            className="w-10 h-10 rounded-xl object-contain bg-muted border border-border shadow-sm"
                        />
                    ) : (
                        <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white font-black text-xl shadow-lg shadow-primary/20">H</div>
                    )}
                    <span className="text-xl font-bold tracking-tight text-foreground">Holkos</span>
                </div>

                <nav className="flex-1 space-y-1.5">
                    {navItems.map((item) => (
                        <SidebarItem
                            key={item.href}
                            {...item}
                            active={isNavItemActive(item.href)}
                        />
                    ))}
                </nav>

                <div className="mt-auto space-y-2">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 font-medium transition-colors"
                    >
                        <LogOut size={18} />
                        <span>Dil</span>
                    </button>
                    <div className="p-4 bg-muted rounded-2xl border border-border">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1.5">Versioni Web</p>
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-bold text-foreground">v1.0.0</p>
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        </div>
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
                            className="fixed inset-y-0 left-0 w-72 bg-card z-50 p-6 shadow-2xl lg:hidden flex flex-col border-r border-border"
                        >
                            <div className="flex items-center justify-between mb-10">
                                <div className="flex items-center gap-3">
                                    {logoUrl ? (
                                        <img
                                            src={logoUrl}
                                            alt="Holkos"
                                            className="w-10 h-10 rounded-xl object-contain bg-muted border border-border shadow-sm"
                                        />
                                    ) : (
                                        <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white font-black shadow-lg shadow-blue-200">H</div>
                                    )}
                                    <span className="text-xl font-bold tracking-tight text-foreground">Holkos</span>
                                </div>
                                <button onClick={() => setSidebarOpen(false)} className="p-2 text-muted-foreground hover:bg-muted rounded-xl"><X size={20} /></button>
                            </div>
                            <nav className="space-y-1.5 flex-1">
                                {navItems.map((item) => (
                                    <SidebarItem
                                        key={item.href}
                                        {...item}
                                        active={isNavItemActive(item.href)}
                                    />
                                ))}
                            </nav>
                            <button
                                onClick={() => { handleLogout(); setSidebarOpen(false); }}
                                className="flex items-center gap-3 px-4 py-3 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 font-medium mt-4 text-foreground"
                            >
                                <LogOut size={20} />
                                <span>Dil</span>
                            </button>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <main className="flex-1 flex flex-col min-w-0">
                <header className="h-16 sm:h-20 bg-card/80 backdrop-blur-xl border-b border-border flex items-center justify-between px-4 sm:px-6 lg:px-10 sticky top-0 z-30">
                    <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-2.5 text-muted-foreground hover:bg-muted rounded-xl transition-colors">
                        <Menu size={22} />
                    </button>

                    <div className="hidden lg:flex items-center relative max-w-md w-full">
                        <Search className="absolute left-4 text-muted-foreground" size={18} />
                        <input
                            type="text"
                            placeholder="Kërko fatura, klientë..."
                            className="w-full bg-muted/50 border border-border rounded-2xl py-2.5 pl-12 pr-4 text-sm focus:ring-2 focus:ring-primary/20 focus:bg-card transition-all placeholder:text-muted-foreground text-foreground"
                        />
                    </div>

                    <div className="flex items-center gap-2 md:gap-3">
                        <button
                            type="button"
                            onClick={() => toggleTheme()}
                            className="p-2.5 text-muted-foreground hover:bg-muted rounded-xl transition-colors"
                            title={isDark ? 'Ndërro në dritë' : 'Ndërro në errësirë'}
                            aria-label={isDark ? 'Ndërro në dritë' : 'Ndërro në errësirë'}
                        >
                            {isDark ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                        <button className="p-2.5 text-muted-foreground hover:bg-muted hover:text-foreground rounded-xl relative transition-all">
                            <Bell size={20} />
                            <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-primary rounded-full ring-2 ring-card"></span>
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-3 py-2.5 text-foreground hover:bg-rose-50 dark:hover:bg-rose-900/20 hover:text-rose-600 dark:hover:text-rose-400 rounded-xl transition-all text-sm font-medium"
                            title="Dil"
                        >
                            <LogOut size={18} />
                            <span className="hidden sm:inline">Dil</span>
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-auto bg-background">
                    <motion.div
                        key={location.pathname}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="h-full"
                    >
                        <Outlet />
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
            <ThemeProvider>
            <AuthProvider>
                <NetworkStatus />
                <ScrollToTop />
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={
                        <ProtectedRoute>
                            <Layout />
                        </ProtectedRoute>
                    }>
                        <Route index element={<Dashboard />} />
                        <Route path="invoices" element={<InvoicesPage />} />
                        <Route path="invoices/new" element={<InvoiceForm />} />
                        <Route path="invoices/edit/:id" element={<InvoiceForm />} />
                        <Route path="offers" element={<OffersPage />} />
                        <Route path="offers/new" element={<OfferForm />} />
                        <Route path="offers/edit/:id" element={<OfferForm />} />
                        <Route path="clients" element={<ClientsPage />} />
                        <Route path="contracts" element={<ContractsPage />} />
                        <Route path="contracts/new" element={<ContractForm />} />
                        <Route path="contracts/edit/:id" element={<ContractForm />} />
                        <Route path="templates" element={<TemplatesPage />} />
                        <Route path="settings" element={<SettingsPage />} />
                    </Route>
                </Routes>
            </AuthProvider>
            </ThemeProvider>
        </Router>
    )
}

export default App
