import { useState, useEffect, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate, Outlet } from 'react-router-dom'
import {
    LayoutDashboard,
    FileText,
    FileSignature,
    Users,
    Settings,
    Briefcase,
    X,
    Search,
    Layers,
    FilePlus,
    Plus,
    LogOut,
    Moon,
    Sun
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { CompanyService, SettingsService, API_BASE } from './services/api'
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
import { ToastProvider } from './components/Toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import { useActivityTracker } from './hooks/useActivityTracker'

const ScrollToTop = () => {
    const location = useLocation()

    useEffect(() => {
        window.scrollTo({ top: 0, left: 0, behavior: 'instant' as ScrollBehavior })
    }, [location.pathname])

    return null
}

const SidebarItem = ({ icon: Icon, label, href, active }: any) => (
    <Link to={href}>
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${active
            ? 'bg-primary/10 text-primary font-semibold shadow-sm'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}>
            <Icon size={20} strokeWidth={active ? 2.5 : 1.8} />
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
    const bottomNavRef = useRef<HTMLElement>(null)
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

    const bottomNavItems = [
        { icon: LayoutDashboard, label: 'Raporte', href: '/' },
        { icon: Layers, label: 'Ofertat', href: '/offers' },
        { icon: FileText, label: 'Faturat', href: '/invoices' },
        { icon: FileSignature, label: 'Kontratat', href: '/contracts' },
        { icon: Users, label: 'Klientët', href: '/clients' },
    ]

    useEffect(() => {
        if (sidebarOpen) {
            setSidebarOpen(false)
        }
    }, [location.pathname])

    useEffect(() => {
        const nav = bottomNavRef.current
        const vv = window.visualViewport
        if (!nav || !vv) return

        // Ruaj lartësinë bazë kur nuk ka tastierë
        let baseHeight = vv.height

        const show = () => { nav.style.display = '' }
        const hide = () => { nav.style.display = 'none' }

        const update = () => {
            const diff = baseHeight - vv.height
            if (diff > 80) {
                // Tastiera u hap — fshih nav
                hide()
            } else {
                // Tastiera u mbyll ose nuk ka — shfaq nav dhe rifresko baseHeight
                show()
                baseHeight = vv.height
            }
        }

        // Rifresko baseHeight kur rrotet ekrani
        const handleOrientation = () => {
            setTimeout(() => { baseHeight = vv.height; show() }, 400)
        }

        vv.addEventListener('resize', update)
        vv.addEventListener('scroll', update)
        window.addEventListener('orientationchange', handleOrientation)

        return () => {
            vv.removeEventListener('resize', update)
            vv.removeEventListener('scroll', update)
            window.removeEventListener('orientationchange', handleOrientation)
            show()
        }
    }, [])

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

    const logoLightUrl = company?.logo_light_path
        ? (API_BASE && API_BASE.startsWith('http')
            ? `${API_BASE.replace(/\/$/, '')}/${company.logo_light_path.replace(/^\/+/, '')}`
            : `/${company.logo_light_path.replace(/^\/+/, '')}`)
        : ''

    const logoDarkUrl = company?.logo_dark_path
        ? (API_BASE && API_BASE.startsWith('http')
            ? `${API_BASE.replace(/\/$/, '')}/${company.logo_dark_path.replace(/^\/+/, '')}`
            : `/${company.logo_dark_path.replace(/^\/+/, '')}`)
        : ''

    // logo_path = PDF (nuk e prekë), logo_light_path / logo_dark_path = UI
    const activeLogo = isDark
        ? (logoDarkUrl || logoLightUrl || logoUrl)
        : (logoLightUrl || logoUrl || logoDarkUrl)

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
                            src={activeLogo}
                            alt="Holkos"
                            className="w-10 h-10 rounded-xl object-contain bg-background"
                        />
                    ) : (
                        <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-black text-xl shadow-lg shadow-indigo-500/25">H</div>
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
                                            src={activeLogo}
                                            alt="Holkos"
                                            className="w-10 h-10 rounded-xl object-contain bg-background"
                                        />
                                    ) : (
                                        <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-black shadow-lg shadow-indigo-500/25">H</div>
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
                <header className="app-header bg-card/90 backdrop-blur-xl border-b border-border flex items-center justify-between px-4 sm:px-6 lg:px-10 sticky top-0 z-30">
                    {/* Mobile: logo + brand name */}
                    <div className="flex items-center gap-2.5 lg:hidden">
                        {logoUrl ? (
                            <img
                                src={activeLogo}
                                alt="Holkos"
                                className="w-8 h-8 rounded-lg object-contain bg-background"
                            />
                        ) : (
                            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-black text-sm shadow-md shadow-indigo-500/30">H</div>
                        )}
                        <span className="text-base font-bold text-foreground tracking-tight">Holkos</span>
                    </div>

                    {/* Desktop: search bar */}
                    <div className="hidden lg:flex items-center relative max-w-md w-full">
                        <Search className="absolute left-4 text-muted-foreground" size={18} />
                        <input
                            type="text"
                            placeholder="Kërko fatura, klientë..."
                            className="w-full bg-muted/50 border border-border rounded-xl py-2.5 pl-12 pr-4 text-sm focus:ring-2 focus:ring-primary/20 focus:bg-card transition-all placeholder:text-muted-foreground text-foreground outline-none"
                        />
                    </div>

                    <div className="flex items-center gap-1.5 md:gap-2">
                        <button
                            type="button"
                            onClick={() => toggleTheme()}
                            className="btn-icon"
                            title={isDark ? 'Ndërro në dritë' : 'Ndërro në errësirë'}
                            aria-label={isDark ? 'Ndërro në dritë' : 'Ndërro në errësirë'}
                        >
                            {isDark ? <Sun size={19} /> : <Moon size={19} />}
                        </button>
                        <Link to="/settings" className="btn-icon" title="Cilësimet">
                            <Settings size={19} />
                        </Link>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-3 py-2 text-muted-foreground hover:bg-rose-50 dark:hover:bg-rose-900/20 hover:text-rose-600 dark:hover:text-rose-400 rounded-xl transition-all text-sm font-medium"
                            title="Dil"
                        >
                            <LogOut size={18} />
                            <span className="hidden sm:inline">Dil</span>
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-auto bg-background pb-nav lg:pb-0">
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

            {/* FAB — mobile only, on invoices/offers */}
            {(location.pathname === '/invoices' || location.pathname === '/offers') && (
                <Link
                    to={location.pathname === '/offers' ? '/offers/new' : '/invoices/new'}
                    className="fab"
                    aria-label="Shto të re"
                >
                    <Plus size={26} strokeWidth={2.5} />
                </Link>
            )}

            {/* Bottom Navigation — mobile only */}
            <nav ref={bottomNavRef} className="bottom-nav">
                {bottomNavItems.map((item) => {
                    const active = isNavItemActive(item.href)
                    return (
                        <Link
                            key={item.href}
                            to={item.href}
                            className={`bottom-nav-item ${active ? 'active' : ''}`}
                        >
                            <item.icon
                                size={22}
                                strokeWidth={active ? 2.5 : 1.8}
                            />
                            <span>{item.label}</span>
                        </Link>
                    )
                })}
            </nav>
        </div>
    )
}

import InvoiceForm from './pages/InvoiceForm'
import Dashboard from './pages/Dashboard'

function App() {
    return (
        <Router>
            <ThemeProvider>
            <AuthProvider>
            <ToastProvider>
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
            </ToastProvider>
            </AuthProvider>
            </ThemeProvider>
        </Router>
    )
}

export default App
