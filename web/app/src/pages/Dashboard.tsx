import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
    FileText, Layers, FileSignature, Users,
    TrendingUp, Calendar, Shield,
    ArrowRight, BarChart2, AlertCircle, Plus,
    RefreshCw, ChevronRight, Zap, Clock
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    Cell
} from 'recharts'
import { DashboardService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { SkeletonStat, Skeleton } from '../components/Skeleton'

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

const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.06 } }
}
const item = {
    hidden: { opacity: 0, y: 14 },
    show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' as const } }
}

const CustomBarTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
        <div className="card-base px-3 py-2.5 text-xs shadow-xl pointer-events-none">
            <p className="font-bold text-muted-foreground mb-1">{label}</p>
            <p className="mono text-primary font-black text-sm">
                {(payload[0].value as number).toLocaleString('sq-AL')} €
            </p>
            <p className="text-muted-foreground mt-0.5">{payload[0].payload.count} fatura</p>
        </div>
    )
}

// Clickable KPI card
const KpiCard = ({ icon: Icon, iconBg, iconColor, label, value, sub, badge, badgeColor, onClick }: {
    icon: any, iconBg: string, iconColor: string, label: string, value: string | number,
    sub?: string, badge?: string, badgeColor?: string, onClick?: () => void
}) => (
    <motion.button
        variants={item}
        onClick={onClick}
        className={`card-hover p-4 sm:p-5 text-left w-full space-y-3 ${onClick ? 'cursor-pointer' : 'cursor-default'}`}
        whileTap={onClick ? { scale: 0.97 } : {}}
    >
        <div className="flex items-start justify-between">
            <div className={`w-9 h-9 rounded-xl ${iconBg} flex items-center justify-center shrink-0`}>
                <Icon size={17} className={iconColor} />
            </div>
            {badge && (
                <span className={`text-[9px] font-black px-2 py-0.5 rounded-full border ${badgeColor}`}>
                    {badge}
                </span>
            )}
        </div>
        <div>
            <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest leading-tight">{label}</p>
            <p className="mono text-xl sm:text-2xl font-black text-foreground mt-0.5 leading-none">{value}</p>
            {sub && <p className="text-[11px] text-muted-foreground font-medium mt-1">{sub}</p>}
        </div>
        {onClick && (
            <div className="flex items-center gap-1 text-[10px] font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                <ChevronRight size={11} /> Shiko
            </div>
        )}
    </motion.button>
)

const Dashboard = () => {
    const navigate = useNavigate()
    const { user } = useAuth()
    const [stats, setStats] = useState<any>(null)
    const [monthly, setMonthly] = useState<any[]>([])
    const [statsLoading, setStatsLoading] = useState(true)
    const [monthlyLoading, setMonthlyLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [activeBar, setActiveBar] = useState<number | null>(null)

    const loadData = (showRefresh = false) => {
        if (showRefresh) setRefreshing(true)

        Promise.allSettled([
            DashboardService.getStats(),
            DashboardService.getMonthly()
        ]).then(([statsRes, monthlyRes]) => {
            if (statsRes.status === 'fulfilled') {
                setStats(statsRes.value)
                localStorage.setItem('dashboard_cache', JSON.stringify(statsRes.value))
            }
            if (monthlyRes.status === 'fulfilled') {
                setMonthly(monthlyRes.value)
                localStorage.setItem('dashboard_monthly_cache', JSON.stringify(monthlyRes.value))
            }
        }).finally(() => {
            setStatsLoading(false)
            setMonthlyLoading(false)
            setRefreshing(false)
        })
    }

    useEffect(() => {
        // Show cache first
        try {
            const cs = localStorage.getItem('dashboard_cache')
            if (cs) { setStats(JSON.parse(cs)); setStatsLoading(false) }
            const cm = localStorage.getItem('dashboard_monthly_cache')
            if (cm) { setMonthly(JSON.parse(cm)); setMonthlyLoading(false) }
        } catch {}
        loadData()
    }, [])

    const greeting = useMemo(() => {
        const h = new Date().getHours()
        if (h < 12) return 'Mirëmëngjes'
        if (h < 18) return 'Mirëdita'
        return 'Mirëmbrëma'
    }, [])

    const dateStr = new Date().toLocaleDateString('sq-AL', {
        weekday: 'long', day: 'numeric', month: 'long'
    })

    const unpaidCount = stats ? (stats.unpaid_count || 0) : 0

    // Highlight current month bar
    const now = new Date()
    const monthNames = ['Jan','Shk','Mar','Pri','Maj','Qer','Kor','Gus','Sht','Tet','Nën','Dhj']
    const currentMonthName = monthNames[now.getMonth()]

    const quickActions = [
        { label: 'Faturë e Re', href: '/invoices/new', icon: FileText, color: 'bg-violet-500 text-white', desc: 'Krijo faturë' },
        { label: 'Ofertë e Re', href: '/offers/new', icon: Layers, color: 'bg-amber-500 text-white', desc: 'Krijo ofertë' },
        { label: 'Klient i Ri', href: '/clients', icon: Users, color: 'bg-emerald-500 text-white', desc: 'Shto klient' },
        { label: 'Kontratë', href: '/contracts/new', icon: FileSignature, color: 'bg-indigo-500 text-white', desc: 'Kontratë e re' },
    ]

    return (
        <div className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto w-full">
            <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">

                {/* ── Header ── */}
                <motion.div variants={item} className="flex items-start justify-between">
                    <div>
                        <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest capitalize">
                            {dateStr}
                        </p>
                        <h1 className="text-2xl sm:text-3xl font-black text-foreground tracking-tight mt-0.5">
                            {greeting},{' '}
                            <span className="bg-gradient-to-r from-violet-600 to-indigo-500 bg-clip-text text-transparent">
                                {user?.username || 'User'}
                            </span>
                        </h1>
                    </div>
                    <button
                        onClick={() => loadData(true)}
                        className="btn-icon mt-1 shrink-0"
                        title="Rifresko"
                    >
                        <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
                    </button>
                </motion.div>

                {/* ── KPI Cards (2×2 → 4×1) ── */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {statsLoading && !stats ? (
                        <><SkeletonStat /><SkeletonStat /><SkeletonStat /><SkeletonStat /></>
                    ) : (
                        <>
                            <KpiCard
                                icon={FileText}
                                iconBg="bg-violet-500/10" iconColor="text-violet-600 dark:text-violet-400"
                                label="Totali Faturave"
                                value={stats?.total_invoices || 0}
                                sub={`${stats?.total_clients || 0} klientë`}
                                badge={stats?.total_offers ? `+${stats.total_offers} oferta` : undefined}
                                badgeColor="bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800"
                                onClick={() => navigate('/invoices')}
                            />
                            <KpiCard
                                icon={Calendar}
                                iconBg="bg-indigo-500/10" iconColor="text-indigo-600 dark:text-indigo-400"
                                label="Ky Muaj"
                                value={stats?.month_invoices || 0}
                                sub={`${(stats?.current_month_revenue || 0).toLocaleString('sq-AL')} €`}
                                badge={stats?.growth !== undefined
                                    ? `${(stats.growth || 0) >= 0 ? '↑' : '↓'} ${Math.abs(stats.growth || 0)}%`
                                    : undefined}
                                badgeColor={`${(stats?.growth || 0) >= 0
                                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                                    : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800'}`}
                                onClick={() => navigate('/invoices')}
                            />
                            <KpiCard
                                icon={TrendingUp}
                                iconBg="bg-emerald-500/10" iconColor="text-emerald-600 dark:text-emerald-400"
                                label="Të Ardhura"
                                value={`${(stats?.total_revenue || 0).toLocaleString('sq-AL')} €`}
                                sub="Të gjitha kohët"
                                badge={unpaidCount > 0 ? `${unpaidCount} pa paguar` : undefined}
                                badgeColor="bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800"
                                onClick={() => navigate('/invoices')}
                            />
                            <KpiCard
                                icon={Shield}
                                iconBg="bg-green-500/10" iconColor="text-green-600 dark:text-green-400"
                                label="TVSH"
                                value={`${(stats?.total_vat || 0).toLocaleString('sq-AL')} €`}
                                sub="Totali TVSH"
                                badgeColor=""
                            />
                        </>
                    )}
                </div>

                {/* ── Unpaid alert (if any) ── */}
                <AnimatePresence>
                    {!statsLoading && unpaidCount > 0 && (
                        <motion.div
                            variants={item}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -8 }}
                        >
                            <button
                                onClick={() => navigate('/invoices')}
                                className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 dark:hover:bg-rose-950/50 transition-colors text-left group"
                            >
                                <div className="w-8 h-8 rounded-xl bg-rose-500/15 flex items-center justify-center shrink-0">
                                    <AlertCircle size={16} className="text-rose-500" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-black text-rose-700 dark:text-rose-400">
                                        {unpaidCount} {unpaidCount === 1 ? 'faturë e papaguar' : 'fatura të papaguara'}
                                    </p>
                                    <p className="text-[11px] text-rose-600/70 dark:text-rose-400/70 font-medium">Kliko për të parë listën</p>
                                </div>
                                <ArrowRight size={15} className="text-rose-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* ── Revenue Chart ── */}
                <motion.div variants={item} className="section-card">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <BarChart2 size={15} className="text-primary" />
                            <h3 className="text-xs font-black text-foreground uppercase tracking-widest">Të Ardhurat — 12 Muajt</h3>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-2.5 h-2.5 rounded-sm bg-primary opacity-40" />
                            <div className="w-2.5 h-2.5 rounded-sm bg-primary" />
                            <span className="text-[10px] text-muted-foreground font-medium ml-0.5">Muaji aktual</span>
                        </div>
                    </div>
                    {monthlyLoading && !monthly.length ? (
                        <Skeleton className="h-40 w-full rounded-xl" />
                    ) : (
                        <ResponsiveContainer width="100%" height={160}>
                            <BarChart
                                data={monthly}
                                margin={{ top: 4, right: 0, left: -24, bottom: 0 }}
                                onMouseLeave={() => setActiveBar(null)}
                            >
                                <XAxis
                                    dataKey="month"
                                    tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                                    axisLine={false} tickLine={false}
                                />
                                <YAxis
                                    tick={{ fontSize: 9, fontFamily: "'JetBrains Mono', monospace", fill: 'hsl(var(--muted-foreground))' }}
                                    axisLine={false} tickLine={false}
                                    tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
                                />
                                <Tooltip
                                    content={<CustomBarTooltip />}
                                    cursor={{ fill: 'hsl(var(--muted))', radius: 4 }}
                                />
                                <Bar
                                    dataKey="revenue"
                                    radius={[4, 4, 0, 0]}
                                    maxBarSize={26}
                                    onMouseEnter={(_, index) => setActiveBar(index)}
                                >
                                    {monthly.map((entry, index) => (
                                        <Cell
                                            key={index}
                                            fill={
                                                entry.month === currentMonthName
                                                    ? 'hsl(var(--primary))'
                                                    : activeBar === index
                                                        ? 'hsl(var(--primary) / 0.7)'
                                                        : 'hsl(var(--primary) / 0.35)'
                                            }
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </motion.div>

                {/* ── Activity Feed + Quick Actions ── */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

                    {/* Activity — 3/5 */}
                    <motion.div variants={item} className="lg:col-span-3 section-card">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Clock size={15} className="text-primary" />
                                <h3 className="text-xs font-black text-foreground uppercase tracking-widest">Aktiviteti i Fundit</h3>
                            </div>
                            <Link to="/invoices" className="flex items-center gap-1 text-[10px] font-bold text-primary hover:text-primary/80 uppercase tracking-widest transition-colors">
                                Të gjitha <ChevronRight size={11} />
                            </Link>
                        </div>

                        {statsLoading && !stats ? (
                            <div className="space-y-2">
                                {[...Array(4)].map((_, i) => (
                                    <div key={i} className="flex items-center gap-3 p-2">
                                        <Skeleton className="w-9 h-9 rounded-xl" />
                                        <div className="flex-1 space-y-1.5">
                                            <Skeleton className="h-3 w-28" />
                                            <Skeleton className="h-2.5 w-16" />
                                        </div>
                                        <Skeleton className="h-4 w-14 rounded-full" />
                                        <Skeleton className="h-4 w-14" />
                                    </div>
                                ))}
                            </div>
                        ) : !stats?.recent_activity?.length ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <div className="w-10 h-10 bg-muted rounded-xl flex items-center justify-center mb-2">
                                    <FileText size={18} className="text-muted-foreground/50" />
                                </div>
                                <p className="text-sm text-muted-foreground italic">Nuk ka aktivitet ende.</p>
                                <Link to="/invoices/new">
                                    <button className="btn-primary mt-3 px-4 py-2 text-xs flex items-center gap-1.5">
                                        <Plus size={13} /> Krijo faturë
                                    </button>
                                </Link>
                            </div>
                        ) : (
                            <div className="space-y-0.5">
                                {stats.recent_activity.map((act: any, idx: number) => {
                                    const grad = avatarGradient(act.client || '')
                                    const isPaid = act.status === 'paid'
                                    const isInvoice = act.type === 'invoice'
                                    const target = isInvoice
                                        ? (act.id ? `/invoices/edit/${act.id}` : '/invoices')
                                        : (act.id ? `/offers/edit/${act.id}` : '/offers')

                                    return (
                                        <motion.button
                                            key={idx}
                                            onClick={() => navigate(target)}
                                            className="w-full flex items-center gap-3 px-2.5 py-2.5 rounded-xl hover:bg-muted/60 active:bg-muted transition-colors text-left group"
                                            whileTap={{ scale: 0.98 }}
                                        >
                                            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center shrink-0 shadow-sm`}>
                                                <span className="text-[11px] font-black text-white">{initials(act.client)}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold text-foreground truncate leading-tight">{act.client}</p>
                                                <p className="mono text-[10px] text-muted-foreground leading-tight">
                                                    #{act.number} · {new Date(act.date).toLocaleDateString('sq-AL')}
                                                </p>
                                            </div>
                                            {isInvoice ? (
                                                <span className={`badge-base shrink-0 ${isPaid ? 'badge-paid' : 'badge-unpaid'}`}>
                                                    {isPaid ? 'Paguar' : 'Pa pag.'}
                                                </span>
                                            ) : (
                                                <span className="badge-base badge-pending shrink-0">Ofertë</span>
                                            )}
                                            <span className="mono text-sm font-black text-foreground shrink-0">
                                                {act.amount.toLocaleString('sq-AL')} €
                                            </span>
                                            <ArrowRight size={13} className="text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 transition-all group-hover:translate-x-0.5" />
                                        </motion.button>
                                    )
                                })}
                            </div>
                        )}
                    </motion.div>

                    {/* Quick Actions — 2/5 */}
                    <motion.div variants={item} className="lg:col-span-2 space-y-3">

                        {/* Create actions */}
                        <div className="section-card">
                            <div className="flex items-center gap-2 mb-3">
                                <Zap size={14} className="text-primary" />
                                <h3 className="text-xs font-black text-foreground uppercase tracking-widest">Krijo të Re</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                {quickActions.map(action => (
                                    <Link key={action.href} to={action.href}>
                                        <motion.div
                                            whileTap={{ scale: 0.95 }}
                                            className="flex flex-col items-center gap-2 p-3 rounded-xl border border-border hover:border-primary/30 hover:bg-muted/50 transition-all cursor-pointer text-center group"
                                        >
                                            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-sm ${action.color}`}>
                                                <action.icon size={16} />
                                            </div>
                                            <div>
                                                <p className="text-[11px] font-black text-foreground leading-tight">{action.label}</p>
                                                <p className="text-[9px] text-muted-foreground font-medium">{action.desc}</p>
                                            </div>
                                        </motion.div>
                                    </Link>
                                ))}
                            </div>
                        </div>

                        {/* Stats mini */}
                        {!statsLoading && stats && (
                            <motion.div
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="section-card space-y-3"
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <TrendingUp size={14} className="text-primary" />
                                    <h3 className="text-xs font-black text-foreground uppercase tracking-widest">Statuset</h3>
                                </div>
                                <div className="space-y-2.5">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                            <span className="text-xs text-muted-foreground font-medium">Të Paguara</span>
                                        </div>
                                        <span className="mono text-xs font-black text-foreground">{stats.paid_count || 0}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-rose-500" />
                                            <span className="text-xs text-muted-foreground font-medium">Të Papaguara</span>
                                        </div>
                                        <span className="mono text-xs font-black text-foreground">{stats.unpaid_count || 0}</span>
                                    </div>
                                    {/* Progress bar */}
                                    {((stats.paid_count || 0) + (stats.unpaid_count || 0)) > 0 && (
                                        <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                                            <motion.div
                                                className="h-full bg-emerald-500 rounded-full"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${((stats.paid_count || 0) / ((stats.paid_count || 0) + (stats.unpaid_count || 0))) * 100}%` }}
                                                transition={{ duration: 0.8, ease: 'easeOut', delay: 0.4 }}
                                            />
                                        </div>
                                    )}
                                </div>
                                <Link to="/invoices" className="flex items-center justify-between pt-1 border-t border-border text-[10px] text-muted-foreground hover:text-primary transition-colors font-bold uppercase tracking-widest">
                                    Shiko faturat <ArrowRight size={10} />
                                </Link>
                            </motion.div>
                        )}
                    </motion.div>
                </div>

            </motion.div>
        </div>
    )
}

export default Dashboard
