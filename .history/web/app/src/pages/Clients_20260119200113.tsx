import { useState, useEffect } from 'react'
import { Plus, Search, User, Mail, Phone, MapPin } from 'lucide-react'
import { ClientService } from '../services/api'
import { motion } from 'framer-motion'

const ClientsPage = () => {
    const [clients, setClients] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        ClientService.getAll()
            .then(data => setClients(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }, [])

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold">Klientët</h1>
                    <p className="text-gray-500 text-sm mt-1">Lista e të gjithë klientëve tuaj të regjistruar.</p>
                </div>
                <button className="flex items-center justify-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-all shadow-lg shadow-blue-200">
                    <Plus size={18} />
                    <span>Shto Klient</span>
                </button>
            </div>

            <div className="mb-6 relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                    type="text"
                    placeholder="Kërko klientët..."
                    className="w-full bg-white border border-gray-100 rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    [1, 2, 3].map(i => (
                        <div key={i} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm animate-pulse">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="w-12 h-12 bg-gray-100 rounded-full"></div>
                                <div className="space-y-2">
                                    <div className="h-4 bg-gray-100 rounded w-32"></div>
                                    <div className="h-3 bg-gray-100 rounded w-20"></div>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <div className="h-3 bg-gray-100 rounded w-full"></div>
                                <div className="h-3 bg-gray-100 rounded w-full"></div>
                            </div>
                        </div>
                    ))
                ) : clients.length === 0 ? (
                    <div className="col-span-full py-20 text-center text-gray-400">
                        Nuk ka klientë të regjistruar.
                    </div>
                ) : (
                    clients.map((client, idx) => (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.05 }}
                            key={client.id}
                            className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-blue-100 transition-all group"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center font-bold text-lg group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                        {client.name.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{client.name}</h3>
                                        <p className="text-xs text-gray-400">ID: {client.unique_number || 'N/A'}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-3 text-sm text-gray-600">
                                {client.email && (
                                    <div className="flex items-center gap-2">
                                        <Mail size={16} className="text-gray-400" />
                                        <span>{client.email}</span>
                                    </div>
                                )}
                                {client.phone && (
                                    <div className="flex items-center gap-2">
                                        <Phone size={16} className="text-gray-400" />
                                        <span>{client.phone}</span>
                                    </div>
                                )}
                                {client.address && (
                                    <div className="flex items-center gap-2">
                                        <MapPin size={16} className="text-gray-400" />
                                        <span className="truncate">{client.address}</span>
                                    </div>
                                )}
                            </div>

                            <div className="mt-6 pt-4 border-t border-gray-50 flex justify-between items-center">
                                <button className="text-blue-600 text-sm font-medium hover:underline">Shiko Detajet</button>
                                <button className="p-1 px-2 bg-gray-50 text-gray-500 rounded-lg text-xs hover:bg-gray-100 transition-colors">Modifiko</button>
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    )
}

export default ClientsPage
