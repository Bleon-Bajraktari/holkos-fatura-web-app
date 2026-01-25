import { useState, useEffect } from 'react'
import { Plus, Search, Download, Briefcase, Eye } from 'lucide-react'
import { OfferService } from '../services/api'
import { motion } from 'framer-motion'

const OffersPage = () => {
    const [offers, setOffers] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        OfferService.getAll()
            .then(data => setOffers(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }, [])

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold">Ofertat</h1>
                    <p className="text-gray-500 text-sm mt-1">Shikoni dhe menaxhoni ofertat e dërguara klientëve.</p>
                </div>
                <button className="flex items-center justify-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-all shadow-lg shadow-blue-200">
                    <Plus size={18} />
                    <span>Ofertë e Re</span>
                </button>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-gray-50 flex flex-col md:flex-row gap-4 items-center justify-between">
                    <div className="relative w-full md:w-96">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Kërko ofertat..."
                            className="w-full bg-gray-50 border-none rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-gray-50/50 text-gray-500 text-xs font-semibold uppercase tracking-wider">
                                <th className="px-6 py-4">Nr. Ofertës</th>
                                <th className="px-6 py-4">Subjekti</th>
                                <th className="px-6 py-4">Klienti</th>
                                <th className="px-6 py-4">Data</th>
                                <th className="px-6 py-4 text-right">Shuma</th>
                                <th className="px-6 py-4"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {loading ? (
                                [1, 2].map(i => (
                                    <tr key={i} className="animate-pulse">
                                        <td className="px-6 py-4"><div className="h-4 bg-gray-100 rounded w-24"></div></td>
                                        <td className="px-6 py-4"><div className="h-4 bg-gray-100 rounded w-48"></div></td>
                                        <td className="px-6 py-4"><div className="h-4 bg-gray-100 rounded w-32"></div></td>
                                        <td className="px-6 py-4"><div className="h-4 bg-gray-100 rounded w-20"></div></td>
                                        <td className="px-6 py-4 text-right"><div className="h-4 bg-gray-100 rounded w-16 ml-auto"></div></td>
                                        <td className="px-6 py-4"></td>
                                    </tr>
                                ))
                            ) : offers.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                                        Nuk ka oferta të regjistruara.
                                    </td>
                                </tr>
                            ) : (
                                offers.map((offer, idx) => (
                                    <motion.tr
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        key={offer.id}
                                        className="hover:bg-gray-50/50 transition-colors group"
                                    >
                                        <td className="px-6 py-4 font-medium text-gray-900">{offer.offer_number}</td>
                                        <td className="px-6 py-4 text-gray-600 truncate max-w-[200px]">{offer.subject}</td>
                                        <td className="px-6 py-4 text-gray-600">{offer.client?.name}</td>
                                        <td className="px-6 py-4 text-gray-500">{new Date(offer.date).toLocaleDateString('sq-AL')}</td>
                                        <td className="px-6 py-4 text-right font-semibold text-gray-900">
                                            {parseFloat(offer.total).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all">
                                                    <Eye size={18} />
                                                </button>
                                                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all">
                                                    <Download size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </motion.tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default OffersPage
