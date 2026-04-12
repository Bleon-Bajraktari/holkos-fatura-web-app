import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Save, Trash2, Edit3, ArrowLeft, Plus, X, Phone, Mail, MapPin, Hash, UserPlus } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { ClientService } from '../services/api'
import ConfirmDialog from '../components/ConfirmDialog'
import { useToast } from '../hooks/useToast'

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

const ClientsPage = () => {
    const navigate = useNavigate()
    const toast = useToast()
    const [clients, setClients] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [selectedId, setSelectedId] = useState<number | string | null>(null)
    const [showForm, setShowForm] = useState(false)
    const [confirmDelete, setConfirmDelete] = useState<{ open: boolean; id?: number | string }>({ open: false })
    const [form, setForm] = useState({
        name: '',
        address: '',
        unique_number: '',
        phone: '',
        email: ''
    })

    const loadClients = () => {
        setLoading(true)
        ClientService.getAll()
            .then(data => setClients(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        loadClients()
    }, [])

    const filtered = clients.filter((c: any) => {
        const term = (search || '').toLowerCase()
        return (String(c?.name ?? '')).toLowerCase().includes(term)
            || (String(c?.unique_number ?? '')).toLowerCase().includes(term)
            || (String(c?.address ?? '')).toLowerCase().includes(term)
    })

    const clearForm = () => {
        setSelectedId(null)
        setShowForm(false)
        setForm({ name: '', address: '', unique_number: '', phone: '', email: '' })
    }

    const handleSave = async () => {
        if (!form.name.trim()) {
            toast.error('Ju lutem shkruani emrin!')
            return
        }
        try {
            if (selectedId) {
                await ClientService.update(selectedId as any, form)
                toast.success('Klienti u përditësua')
            } else {
                await ClientService.create(form)
                toast.success('Klienti u ruajt')
            }
            clearForm()
            loadClients()
        } catch {
            toast.error('Gabim gjatë ruajtjes')
        }
    }

    const handleEdit = (client: any) => {
        setSelectedId(client.id)
        setForm({
            name: client.name || '',
            address: client.address || '',
            unique_number: client.unique_number || '',
            phone: client.phone || '',
            email: client.email || ''
        })
        setShowForm(true)
    }

    const handleDelete = async (id: number | string) => {
        try {
            await ClientService.delete(id as any)
            toast.success('Klienti u fshi')
            loadClients()
        } catch {
            toast.error('Gabim gjatë fshirjes')
        }
    }

    return (
        <div className="min-h-screen pb-24">
            {/* Sticky Header */}
            <div className="bg-card/95 backdrop-blur-xl border-b border-border sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 min-w-0">
                            <button onClick={() => navigate('/')} className="btn-icon shrink-0">
                                <ArrowLeft size={18} />
                            </button>
                            <div>
                                <h1 className="text-lg sm:text-xl font-black text-foreground tracking-tight">
                                    <span className="text-primary">Klientët</span>
                                </h1>
                                <p className="text-[11px] text-muted-foreground font-medium hidden sm:block">
                                    {clients.length} klientë gjithsej
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => { clearForm(); setShowForm(true) }}
                            className="btn-primary flex items-center gap-2 px-4 py-2.5 text-sm"
                        >
                            <UserPlus size={15} />
                            <span className="hidden sm:inline">Klient i Ri</span>
                            <span className="sm:hidden">Shto</span>
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-3 sm:px-6 mt-4">
                {/* Add/Edit Form */}
                <AnimatePresence>
                    {showForm && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.25 }}
                            className="overflow-hidden mb-4"
                        >
                            <div className="card-base p-4 sm:p-6 border-primary/30 bg-primary/5">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-black text-foreground text-sm">
                                        {selectedId ? 'Ndrysho Klientin' : 'Klient i Ri'}
                                    </h3>
                                    <button onClick={clearForm} className="btn-icon p-1.5">
                                        <X size={16} />
                                    </button>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <div>
                                        <label className="input-label">Emri i Klientit *</label>
                                        <input
                                            type="text"
                                            value={form.name}
                                            onChange={e => setForm({ ...form, name: e.target.value })}
                                            className="input-base"
                                            placeholder="Emri i plotë..."
                                            autoFocus
                                        />
                                    </div>
                                    <div>
                                        <label className="input-label">Adresa</label>
                                        <input
                                            type="text"
                                            value={form.address}
                                            onChange={e => setForm({ ...form, address: e.target.value })}
                                            className="input-base"
                                            placeholder="Qyteti, Shteti..."
                                        />
                                    </div>
                                    <div>
                                        <label className="input-label">Numri Unik (NUI/NIPT)</label>
                                        <input
                                            type="text"
                                            value={form.unique_number}
                                            onChange={e => setForm({ ...form, unique_number: e.target.value })}
                                            className="input-base"
                                            placeholder="811234567"
                                        />
                                    </div>
                                    <div>
                                        <label className="input-label">Telefoni</label>
                                        <input
                                            type="text"
                                            value={form.phone}
                                            onChange={e => setForm({ ...form, phone: e.target.value })}
                                            className="input-base"
                                            placeholder="+383 44 123 456"
                                        />
                                    </div>
                                    <div className="sm:col-span-2">
                                        <label className="input-label">Email</label>
                                        <input
                                            type="email"
                                            value={form.email}
                                            onChange={e => setForm({ ...form, email: e.target.value })}
                                            className="input-base"
                                            placeholder="info@kompania.com"
                                        />
                                    </div>
                                </div>
                                <div className="flex gap-2 mt-4">
                                    <button onClick={handleSave} className="btn-primary flex items-center gap-2 px-5 py-2.5 text-sm">
                                        <Save size={15} />
                                        {selectedId ? 'Përditëso' : 'Ruaj'}
                                    </button>
                                    <button onClick={clearForm} className="btn-secondary px-5 py-2.5 text-sm">
                                        Anulo
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Search */}
                <div className="search-bar mb-4">
                    <Search className="text-muted-foreground shrink-0 ml-1" size={16} />
                    <input
                        type="text"
                        placeholder="Kërko klientët..."
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

                {/* Client Cards Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {[...Array(6)].map((_, i) => (
                            <div key={i} className="card-base p-4 space-y-3">
                                <div className="flex items-center gap-3">
                                    <div className="skeleton w-10 h-10 rounded-xl" />
                                    <div className="space-y-1.5 flex-1">
                                        <div className="skeleton h-3 w-32" />
                                        <div className="skeleton h-2.5 w-20" />
                                    </div>
                                </div>
                                <div className="skeleton h-2.5 w-full" />
                                <div className="skeleton h-2.5 w-3/4" />
                            </div>
                        ))}
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="card-base p-16 text-center">
                        <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <UserPlus size={28} className="text-muted-foreground/50" />
                        </div>
                        <h3 className="text-base font-bold text-foreground">Nuk u gjetën klientë</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            {search ? 'Provo të ndryshosh kërkimin.' : 'Shto klientin tuaj të parë.'}
                        </p>
                        {!search && (
                            <button
                                onClick={() => { clearForm(); setShowForm(true) }}
                                className="btn-primary mt-4 px-5 py-2.5 text-sm flex items-center gap-2 mx-auto"
                            >
                                <Plus size={15} /> Shto Klient
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {filtered.map((client: any) => {
                            const grad = avatarGradient(client.name || '')
                            return (
                                <motion.div
                                    key={client.id}
                                    layout
                                    initial={{ opacity: 0, scale: 0.97 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="card-base p-4 hover:shadow-card-hover hover:border-primary/20 transition-all duration-200"
                                >
                                    {/* Card Header */}
                                    <div className="flex items-start gap-3 mb-3">
                                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center shrink-0 shadow-sm`}>
                                            <span className="text-[12px] font-black text-white">{initials(client.name)}</span>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-black text-foreground text-sm truncate">{client.name}</div>
                                            {client.unique_number && (
                                                <div className="text-[10px] text-muted-foreground font-bold mono mt-0.5 flex items-center gap-1">
                                                    <Hash size={9} /> {client.unique_number}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Details */}
                                    <div className="space-y-1.5 text-[11px] text-muted-foreground mb-4">
                                        {client.address && (
                                            <div className="flex items-center gap-1.5">
                                                <MapPin size={11} className="shrink-0" />
                                                <span className="truncate">{client.address}</span>
                                            </div>
                                        )}
                                        {client.phone && (
                                            <div className="flex items-center gap-1.5">
                                                <Phone size={11} className="shrink-0" />
                                                <span>{client.phone}</span>
                                            </div>
                                        )}
                                        {client.email && (
                                            <div className="flex items-center gap-1.5">
                                                <Mail size={11} className="shrink-0" />
                                                <span className="truncate">{client.email}</span>
                                            </div>
                                        )}
                                        {!client.address && !client.phone && !client.email && (
                                            <div className="text-muted-foreground/50 italic">Pa detaje kontakti</div>
                                        )}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2 pt-3 border-t border-border">
                                        <button
                                            onClick={() => handleEdit(client)}
                                            className="btn-secondary flex-1 flex items-center justify-center gap-1.5 py-2 text-xs"
                                        >
                                            <Edit3 size={13} /> Ndrysho
                                        </button>
                                        <button
                                            onClick={() => setConfirmDelete({ open: true, id: client.id })}
                                            className="btn-icon p-2 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:border-rose-200 dark:hover:border-rose-800"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </motion.div>
                            )
                        })}
                    </div>
                )}
            </div>

            <ConfirmDialog
                isOpen={confirmDelete.open}
                title="Fshi klientin"
                message="A jeni të sigurt se doni të fshini këtë klient? Ky veprim është i pakthyeshëm."
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

export default ClientsPage
