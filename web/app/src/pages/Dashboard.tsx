import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    FileText, Layers, FileSignature, Users, Settings,
    TrendingUp, TrendingDown, Calendar, Shield,
    ArrowRight, BarChart2, PieChart as PieChartIcon,
    Activity, Plus
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell
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
    show: { opacity: 1, transition: { staggerChildren: 0.07 } }
}
const item = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' as const } }
}

const CustomBarTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
        <div className="card-base px-3 py-2.5 text-xs shadow-lg">
            <p className="font-bold text-foreground mb-1">{label}</p>
            <p className="mono text-primary font-bold text-sm">
                {(payload[0].value as number).toLocaleString('sq-AL')} €
            </p>
            <p className="text-muted-foreground mt-0.5">{payload[0].payload.count} fatura</p>
        </div>
    )
}

const Dashboard = () => {
    const navigate = useNavigate()
    const { user } = useAuth()
    const [stats, setStats] = useState<any>(null)
    const [monthly, setMonthly] = useState<any[]>([])
    const [statsLoading, setStatsLoading] = useState(true)
    const [monthlyLoading, setMonthlyLoading] = useState(true)

    useEffect(() => {
        // Stats
        DashboardService.getStats()
            .then(data => {
                setStats(data)
                localStorage.setItem('dashboard_cache', JSON.stringify(data))
            })
            .catch(() => {
                const cached = localStorage.getItem('dashboard_cache')
                if (cached) setStats(JSON.parse(cached))
            })
            .finally(() => setStatsLoading(false))

        // Monthly
        DashboardService.getMonthly()
            .then(data => setMonthly(data))
            .catch(() => {
                const cached = localStorage.getItem('dashboard_monthly_cache')
                if (cached) setMonthly(JSON.parse(cached))
            })
            .finally(() => setMonthlyLoading(false))
    }, [])

    const greeting = useMemo(() => {
        const h = new Date().getHours()
        if (h < 12) return 'Mirëmëngjes'
        if (h < 18) return 'Mirëdita'
        return 'Mirëmbrëma'
    }, [])

    const dateStr = new Date().toLocaleDateString('sq-AL', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    })

    const donutData = stats ? [
        { name: 'Të Paguara', value: stats.paid_count || 0, color: '#10b981' },
        { name: 'Të Papaguara', value: stats.unpaid_count || 0, color: '#f43f5e' },
    ] : []
    const donutTotal = donutData.reduce((s, d) => s + d.value, 0)

    const quickActions = [
        { label: 'Faturat', href: '/invoices', icon: FileText, color: 'bg-violet-500/10 text-violet-600 dark:text-violet-400' },
        { label: 'Ofertat', href: '/offers', icon: Layers, color: 'bg-amber-500/10 text-amber-600 dark:text-amber-400' },
        { label: 'Kontratat', href: '/contracts', icon: FileSignature, color: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400' },
        { label: 'Klientë', href: '/clients', icon: Users, color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' },
        { label: 'Cilësime', href: '/settings', icon: Settings, color: 'bg-rose-500/10 text-rose-600 dark:text-rose-400' },
    ]

    return (
        <div className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto w-full">
            <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">

                {/* ── Header ── */}
                <motion.header variants={item}>
                    <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest capitalize">
                        {dateStr}
                    </p>
                    <h1 className="text-2xl sm:text-3xl font-black text-foreground tracking-tight mt-0.5">
                        {greeting},{' '}
                        <span className="gradient-text">{user?.username || 'User'}</span>
                    </h1>
                </motion.header>

                {/* ── KPI Cards ── */}
                <motion.div variants={item} className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {statsLoading ? (
                        <>
                            <SkeletonStat /><SkeletonStat /><SkeletonStat /><SkeletonStat />
                        </>
                    ) : (
                        <>
                            {/* Card 1 — Total Fatura */}
                            <motion.button
                                type="button"
                                onClick={() => navigate('/invoices')}
                                whileHover={{ y: -3 }}
                                whileTap={{ scale: 0.985 }}
                                transition={{ type: 'spring', stiffness: 420, damping: 28 }}
                                className="card-hover p-4 sm:p-5 space-y-3 text-left w-full cursor-pointer"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="w-10 h-10 rounded-2xl bg-violet-500/10 flex items-center justify-center">
                                        <FileText size={18} className="text-violet-600 dark:text-violet-400" />
                                    </div>
                                    {stats?.total_offers > 0 && (
                                        <span className="text-[9px] font-black px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                                            +{stats.total_offers} oferta
                                        </span>
                                    )}
                                </div>
                                <div>
                                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Totali Faturave</p>
                                    <p className="mono text-2xl font-black text-foreground leading-tight mt-0.5">{stats?.total_invoices || 0}</p>
                                </div>
                                <div className="text-[10px] text-muted-foreground font-medium">
                                    {stats?.total_clients || 0} klientë
                                </div>
                            </motion.button>

                            {/* Card 2 — Ky Muaj */}
                            <motion.button
                                type="button"
                                onClick={() => navigate('/invoices')}
                                whileHover={{ y: -3 }}
                                whileTap={{ scale: 0.985 }}
                                transition={{ type: 'spring', stiffness: 420, damping: 28 }}
                                className="card-hover p-4 sm:p-5 space-y-3 text-left w-full cursor-pointer"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
                                        <Calendar size={18} className="text-indigo-600 dark:text-indigo-400" />
                                    </div>
                                    <span className={`inline-flex items-center gap-0.5 text-[9px] font-black px-2 py-0.5 rounded-full border ${
                                        (stats?.growth || 0) >= 0
                                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                                            : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800'
                                    }`}>
                                        {(stats?.growth || 0) >= 0
                                            ? <TrendingUp size={9} />
                                            : <TrendingDown size={9} />
                                        }
                                        {Math.abs(stats?.growth || 0)}%
                                    </span>
                                </div>
                                <div>
                                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Ky Muaj</p>
                                    <p className="mono text-2xl font-black text-foreground leading-tight mt-0.5">{stats?.month_invoices || 0}</p>
                                </div>
                                <div className="mono text-[11px] text-muted-foreground font-medium">
                                    {(stats?.current_month_revenue || 0).toLocaleString('sq-AL')} €
                                </div>
                            </motion.button>

                            {/* Card 3 — Të Ardhura */}
                            <motion.button
                                type="button"
                                onClick={() => navigate('/invoices')}
                                whileHover={{ y: -3 }}
                                whileTap={{ scale: 0.985 }}
                                transition={{ type: 'spring', stiffness: 420, damping: 28 }}
                                className="card-hover p-4 sm:p-5 space-y-3 text-left w-full cursor-pointer"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
                                        <TrendingUp size={18} className="text-emerald-600 dark:text-emerald-400" />
                                    </div>
                                    {(stats?.growth || 0) !== 0 && (
                                        <span className={`inline-flex items-center gap-0.5 text-[9px] font-black px-2 py-0.5 rounded-full border ${
                                            (stats?.growth || 0) >= 0
                                                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                                                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800'
                                        }`}>
                                            {(stats?.growth || 0) >= 0 ? '↑' : '↓'} {Math.abs(stats?.growth || 0)}%
                                        </span>
                                    )}
                                </div>
                                <div>
                                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Të Ardhura</p>
                                    <p className="mono text-xl sm:text-2xl font-black text-foreground leading-tight mt-0.5">
                                        {(stats?.total_revenue || 0).toLocaleString('sq-AL')} €
                                    </p>
                                </div>
                                <div className="text-[10px] text-muted-foreground font-medium">Të gjitha kohët</div>
                            </motion.button>

                            {/* Card 4 — TVSH */}
                            <motion.button
                                type="button"
                                onClick={() => navigate('/invoices')}
                                whileHover={{ y: -3 }}
                                whileTap={{ scale: 0.985 }}
                                transition={{ type: 'spring', stiffness: 420, damping: 28 }}
                                className="card-hover p-4 sm:p-5 space-y-3 text-left w-full cursor-pointer"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="w-10 h-10 rounded-2xl bg-green-500/10 flex items-center justify-center">
                                        <Shield size={18} className="text-green-600 dark:text-green-400" />
                                    </div>
                                    <span className="text-[9px] font-black px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                                        TVSH
                                    </span>
                                </div>
                                <div>
                                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">TVSH e Grumbulluar</p>
                                    <p className="mono text-xl sm:text-2xl font-black text-foreground leading-tight mt-0.5">
                                        {(stats?.total_vat || 0).toLocaleString('sq-AL')} €
                                    </p>
                                </div>
                                <div className="text-[10px] text-muted-foreground font-medium">Totali gjithsej</div>
                            </motion.button>
                        </>
                    )}
                </motion.div>

                {/* ── Charts Row ── */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">

                    {/* Bar Chart — 3/5 */}
                    <motion.div
                        variants={item}
                        whileHover={{ y: -2 }}
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                        className="md:col-span-3 section-card cursor-default"
                    >
                        <div className="flex items-center gap-2 mb-5">
                            <BarChart2 size={16} className="text-primary shrink-0" />
                            <h3 className="text-xs font-black text-foreground uppercase tracking-widest">
                                Të Ardhurat — 12 Muajt e Fundit
                            </h3>
                        </div>
                        {monthlyLoading ? (
                            <Skeleton className="h-44 w-full rounded-xl" />
                        ) : monthly.length === 0 ? (
                            <div className="h-44 flex items-center justify-center text-sm text-muted-foreground italic">
                                Nuk ka të dhëna akoma.
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height={176}>
                                <BarChart data={monthly} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
                                    <XAxis
                                        dataKey="month"
                                        tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                                        axisLine={false}
                                        tickLine={false}
                                    />
                                    <YAxis
                                        tick={{ fontSize: 9, fontFamily: "'JetBrains Mono', monospace", fill: 'hsl(var(--muted-foreground))' }}
                                        axisLine={false}
                                        tickLine={false}
                                        tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
                                    />
                                    <Tooltip content={<CustomBarTooltip />} cursor={{ fill: 'hsl(var(--muted))', radius: 4 }} />
                                    <Bar
                                        dataKey="revenue"
                                        fill="hsl(var(--primary))"
                                        radius={[4, 4, 0, 0]}
                                        maxBarSize={28}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </motion.div>

                    {/* Donut — 2/5 */}
                    <motion.div
                        variants={item}
                        whileHover={{ y: -2 }}
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                        className="md:col-span-2 section-card cursor-default"
                    >
                        <div className="flex items-center gap-2 mb-5">
                            <PieChartIcon size={16} className="text-primary shrink-0" />
                            <h3 className="text-xs font-black text-foreground uppercase tracking-widest">
                                Statusi i Faturave
                            </h3>
                        </div>
                        {statsLoading ? (
                            <div className="flex items-center justify-center py-4">
                                <Skeleton className="w-32 h-32 rounded-full" />
                            </div>
                        ) : donutTotal === 0 ? (
                            <div className="flex items-center justify-center h-32 text-sm text-muted-foreground italic">
                                Nuk ka fatura.
                            </div>
                        ) : (
                            <div className="flex flex-col items-center gap-4">
                                <ResponsiveContainer width={120} height={120}>
                                    <PieChart>
                                        <Pie
                                            data={donutData}
                                            cx="50%" cy="50%"
                                            innerRadius={36} outerRadius={54}
                                            paddingAngle={3}
                                            dataKey="value"
                                            strokeWidth={0}
                                        >
                                            {donutData.map((entry, i) => (
                                                <Cell key={i} fill={entry.color} />
                                            ))}
                                        </Pie>
                                    </PieChart>
                                </ResponsiveContainer>
                                <div className="w-full space-y-2">
                                    {donutData.map(d => (
                                        <div key={d.name} className="flex items-center justify-between gap-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: d.color }} />
                                                <span className="text-xs text-muted-foreground font-medium">{d.name}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="mono text-xs font-bold text-foreground">{d.value}</span>
                                                <span className="text-[9px] text-muted-foreground">
                                                    {donutTotal > 0 ? Math.round((d.value / donutTotal) * 100) : 0}%
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </div>

                {/* ── Activity + Quick Actions ── */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                    {/* Activity Feed — 2/3 */}
                    <motion.div
                        variants={item}
                        whileHover={{ y: -1 }}
                        transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                        className="lg:col-span-2 section-card"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Activity size={16} className="text-primary shrink-0" />
                                <h3 className="text-xs font-black text-foreground uppercase tracking-widest">
                                    Aktiviteti i Fundit
                                </h3>
                            </div>
                            <Link to="/invoices" className="text-[10px] font-bold text-primary hover:text-primary/80 uppercase tracking-widest transition-colors">
                                Shiko të gjitha
                            </Link>
                        </div>

                        {statsLoading ? (
                            <div className="space-y-3">
                                {[...Array(4)].map((_, i) => (
                                    <div key={i} className="flex items-center gap-3 p-3">
                                        <Skeleton className="w-9 h-9 rounded-xl shrink-0" />
                                        <div className="flex-1 space-y-1.5">
                                            <Skeleton className="h-3 w-32" />
                                            <Skeleton className="h-2.5 w-20" />
                                        </div>
                                        <Skeleton className="h-5 w-14 rounded-full" />
                                        <Skeleton className="h-4 w-16" />
                                    </div>
                                ))}
                            </div>
                        ) : !stats?.recent_activity?.length ? (
                            <p className="text-center py-10 text-muted-foreground text-sm italic">
                                Nuk ka aktivitet të fundit.
                            </p>
                        ) : (
                            <div className="space-y-1">
                                {stats.recent_activity.map((act: any, idx: number) => {
                                    const grad = avatarGradient(act.client || '')
                                    const isPaid = act.status === 'paid'
                                    const isInvoice = act.type === 'invoice'
                                    const goToDocument = () => {
                                        if (act.id != null) {
                                            navigate(isInvoice ? `/invoices/edit/${act.id}` : `/offers/edit/${act.id}`)
                                        } else {
                                            navigate(isInvoice ? '/invoices' : '/offers')
                                        }
                                    }
                                    return (
                                        <motion.button
                                            type="button"
                                            key={act.id != null ? `${act.type}-${act.id}` : idx}
                                            onClick={goToDocument}
                                            whileHover={{ x: 3 }}
                                            whileTap={{ scale: 0.99 }}
                                            transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-muted/60 transition-colors text-left group"
                                        >
                                            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center shrink-0 shadow-sm`}>
                                                <span className="text-[11px] font-black text-white">{initials(act.client)}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold text-foreground truncate">{act.client}</p>
                                                <p className="mono text-[10px] text-muted-foreground">
                                                    #{act.number} · {new Date(act.date).toLocaleDateString('sq-AL')}
                                                </p>
                                            </div>
                                            {isInvoice && (
                                                <span className={`badge-base shrink-0 ${isPaid ? 'badge-paid' : 'badge-unpaid'}`}>
                                                    {isPaid ? 'Paguar' : 'Pa paguar'}
                                                </span>
                                            )}
                                            {!isInvoice && (
                                                <span className="badge-base badge-pending shrink-0">Ofertë</span>
                                            )}
                                            <span className="mono text-sm font-black text-foreground shrink-0">
                                                {act.amount.toLocaleString('sq-AL')} €
                                            </span>
                                            <ArrowRight size={14} className="text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </motion.button>
                                    )
                                })}
                            </div>
                        )}
                    </motion.div>

                    {/* Quick Actions — 1/3 */}
                    <motion.div
                        variants={item}
                        whileHover={{ y: -1 }}
                        transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                        className="section-card"
                    >
                        <div className="flex items-center gap-2 mb-4">
                            <Plus size={16} className="text-primary shrink-0" />
                            <h3 className="text-xs font-black text-foreground uppercase tracking-widest">
                                Veprime të Shpejta
                            </h3>
                        </div>
                        <div className="space-y-2">
                            {quickActions.map(action => (
                                <Link
                                    key={action.href}
                                    to={action.href}
                                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-border hover:border-primary/30 hover:bg-muted/50 transition-all group"
                                >
                                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${action.color}`}>
                                        <action.icon size={15} />
                                    </div>
                                    <span className="text-sm font-bold text-foreground flex-1">{action.label}</span>
                                    <ArrowRight size={13} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                </Link>
                            ))}
                        </div>
                    </motion.div>

                </div>
            </motion.div>
        </div>
    )
}

export default Dashboard
