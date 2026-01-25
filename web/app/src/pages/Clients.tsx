import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Save, Trash2, Edit3, ArrowLeft } from 'lucide-react'
import { ClientService } from '../services/api'

const ClientsPage = () => {
    const navigate = useNavigate()
    const [clients, setClients] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [selectedId, setSelectedId] = useState<number | null>(null)
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
        const term = search.toLowerCase()
        return c.name.toLowerCase().includes(term)
            || (c.unique_number || '').toLowerCase().includes(term)
            || (c.address || '').toLowerCase().includes(term)
    })

    const clearForm = () => {
        setSelectedId(null)
        setForm({ name: '', address: '', unique_number: '', phone: '', email: '' })
    }

    const handleSave = async () => {
        if (!form.name.trim()) {
            alert('Ju lutem shkruani emrin!')
            return
        }
        if (selectedId) {
            await ClientService.update(selectedId, form)
        } else {
            await ClientService.create(form)
        }
        clearForm()
        loadClients()
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
    }

    const handleDelete = async (id: number) => {
        if (!confirm('Jeni të sigurt?')) return
        await ClientService.delete(id)
        loadClients()
    }

    return (
        <div className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto w-full">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2.5 bg-white border border-gray-200 rounded-xl text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-all shadow-sm"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold">Menaxhimi i Klientëve</h1>
                        <p className="text-gray-500 text-sm mt-1">Shtoni dhe menaxhoni klientët tuaj</p>
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-6 mb-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-bold text-gray-500">Emri i Klientit</label>
                        <input
                            type="text"
                            value={form.name}
                            onChange={e => setForm({ ...form, name: e.target.value })}
                            className="w-full bg-gray-50 border border-gray-100 rounded-xl py-2.5 px-4 text-sm mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-500">Adresa</label>
                        <input
                            type="text"
                            value={form.address}
                            onChange={e => setForm({ ...form, address: e.target.value })}
                            className="w-full bg-gray-50 border border-gray-100 rounded-xl py-2.5 px-4 text-sm mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-500">Numri Unik</label>
                        <input
                            type="text"
                            value={form.unique_number}
                            onChange={e => setForm({ ...form, unique_number: e.target.value })}
                            className="w-full bg-gray-50 border border-gray-100 rounded-xl py-2.5 px-4 text-sm mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-500">Telefoni</label>
                        <input
                            type="text"
                            value={form.phone}
                            onChange={e => setForm({ ...form, phone: e.target.value })}
                            className="w-full bg-gray-50 border border-gray-100 rounded-xl py-2.5 px-4 text-sm mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-500">Email</label>
                        <input
                            type="email"
                            value={form.email}
                            onChange={e => setForm({ ...form, email: e.target.value })}
                            className="w-full bg-gray-50 border border-gray-100 rounded-xl py-2.5 px-4 text-sm mt-1"
                        />
                    </div>
                </div>
                <div className="mt-4 flex flex-col sm:flex-row sm:items-center gap-2">
                    <button onClick={handleSave} className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 inline-flex items-center justify-center gap-2">
                        <Save size={16} /> {selectedId ? 'Përditëso' : 'Ruaj Klientin'}
                    </button>
                    <button onClick={clearForm} className="w-full sm:w-auto px-4 py-2 bg-gray-50 text-gray-600 rounded-xl text-sm font-bold hover:bg-gray-100">
                        Pastro
                    </button>
                </div>
            </div>

            <div className="mb-4 relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                    type="text"
                    placeholder="Kërko klientët..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full bg-white border border-gray-100 rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm"
                />
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="md:hidden divide-y divide-gray-100">
                    {loading ? (
                        <div className="p-6 text-center text-gray-400">Duke u ngarkuar...</div>
                    ) : filtered.length === 0 ? (
                        <div className="p-6 text-center text-gray-400">Nuk u gjet asnjë klient.</div>
                    ) : (
                        filtered.map((client: any) => (
                            <div key={client.id} className="p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <div className="font-bold text-gray-900">{client.name}</div>
                                        <div className="text-xs text-gray-500">{client.unique_number || '-'}</div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button onClick={() => handleEdit(client)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                                            <Edit3 size={16} />
                                        </button>
                                        <button onClick={() => handleDelete(client.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                                <div className="mt-3 text-sm text-gray-600 space-y-1">
                                    <div>Adresa: {client.address || '-'}</div>
                                    <div>Telefoni: {client.phone || '-'}</div>
                                    <div>Email: {client.email || '-'}</div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
                <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-gray-50/50 text-gray-500 text-xs font-semibold uppercase tracking-wider">
                                <th className="px-6 py-4">Emri</th>
                                <th className="px-6 py-4">Adresa</th>
                                <th className="px-6 py-4">Numri Unik</th>
                                <th className="px-6 py-4">Telefoni</th>
                                <th className="px-6 py-4">Email</th>
                                <th className="px-6 py-4 text-right">Veprimet</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {loading ? (
                                <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-400">Duke u ngarkuar...</td></tr>
                            ) : filtered.length === 0 ? (
                                <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-400">Nuk u gjet asnjë klient.</td></tr>
                            ) : (
                                filtered.map((client: any) => (
                                    <tr key={client.id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-gray-900">{client.name}</td>
                                        <td className="px-6 py-4 text-gray-600">{client.address || '-'}</td>
                                        <td className="px-6 py-4 text-gray-600">{client.unique_number || '-'}</td>
                                        <td className="px-6 py-4 text-gray-600">{client.phone || '-'}</td>
                                        <td className="px-6 py-4 text-gray-600">{client.email || '-'}</td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="inline-flex items-center gap-2">
                                                <button onClick={() => handleEdit(client)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                                                    <Edit3 size={16} />
                                                </button>
                                                <button onClick={() => handleDelete(client.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default ClientsPage
