import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
    Save,
    FileDown,
    Mail,
    Plus,
    Trash2,
    ArrowLeft,
    Search,
    UserPlus,
    Calculator,
    Copy,
    Briefcase,
    Users
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { InvoiceService, OfferService, ClientService } from '../services/api'

interface InvoiceItem {
    id?: number
    description: string
    quantity: number
    unit_price: number
    unit?: string
}

const InvoiceForm = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const location = useLocation()

    const isOffer = location.pathname.startsWith('/offers')
    const service = isOffer ? OfferService : InvoiceService
    const isEdit = !!id

    const [clients, setClients] = useState<any[]>([])
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [showSuggestions, setShowSuggestions] = useState(false)

    const [invoice, setInvoice] = useState({
        invoice_number: '',
        offer_number: '',
        subject: '',
        description: '',
        date: new Date().toISOString().split('T')[0],
        payment_due_date: '',
        client_id: 0,
        client_name: '',
        vat_percentage: 18,
        items: [{ description: '', quantity: 1, unit_price: 0, unit: 'Copa' }] as InvoiceItem[]
    })

    useEffect(() => {
        ClientService.getAll().then(data => setClients(data))

        if (isEdit) {
            setLoading(true)
            service.getOne(parseInt(id))
                .then(data => {
                    setInvoice({
                        ...data,
                        client_name: data.client?.name || ''
                    })
                })
                .finally(() => setLoading(false))
        } else {
            // Fetch next number from backend
            const endpoint = isOffer ? '/api/offers/next-number' : '/api/invoices/next-number'
            fetch(endpoint)
                .then(res => res.json())
                .then(data => setInvoice(prev => ({ ...prev, [isOffer ? 'offer_number' : 'invoice_number']: data.next_number })))
        }
    }, [id, isEdit, isOffer, service])

    const calculateSubtotal = () => {
        return invoice.items.reduce((acc, item) => acc + (item.quantity * item.unit_price), 0)
    }

    const subtotal = calculateSubtotal()
    const vatAmount = subtotal * (invoice.vat_percentage / 100)
    const total = subtotal + vatAmount

    const addItemRow = () => {
        setInvoice(prev => ({
            ...prev,
            items: [...prev.items, { description: '', quantity: 1, unit_price: 0 }]
        }))
    }

    const removeItemRow = (index: number) => {
        if (invoice.items.length === 1) return
        const newItems = [...invoice.items]
        newItems.splice(index, 1)
        setInvoice(prev => ({ ...prev, items: newItems }))
    }

    const updateItem = (index: number, field: keyof InvoiceItem, value: any) => {
        const newItems = [...invoice.items]
        newItems[index] = { ...newItems[index], [field]: value }
        setInvoice(prev => ({ ...prev, items: newItems }))
    }

    const handleSave = async (action: 'save' | 'pdf' | 'email') => {
        if (!invoice.client_id) {
            alert('Ju lutem zgjidhni një klient!')
            return
        }
        if (invoice.items.some(item => !item.description || item.quantity <= 0)) {
            alert('Ju lutem plotësoni artikujt saktë!')
            return
        }

        setSaving(true)
        try {
            const data = {
                ...invoice,
                subtotal,
                vat_amount: vatAmount,
                total
            }
            let savedDoc;
            if (isEdit) {
                savedDoc = await service.create(data) // Should be update, using create for now
            } else {
                savedDoc = await service.create(data)
            }

            if (action === 'pdf') {
                const pdfEndpoint = isOffer ? `/api/offers/${savedDoc.id}/pdf` : `/api/invoices/${savedDoc.id}/pdf`
                window.open(pdfEndpoint, '_blank')
            } else if (action === 'email') {
                alert('Funksioni i Email-it do të hapet së shpejti.')
            }

            navigate(isOffer ? '/offers' : '/invoices')
        } catch (error) {
            console.error('Error saving:', error)
            alert('Gabim gjatë ruajtjes!')
        } finally {
            setSaving(false)
        }
    }

    const filteredClients = clients.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.unique_number?.toLowerCase().includes(searchTerm.toLowerCase())
    )

    if (loading) return <div className="p-8 text-center text-gray-500">Duke u ngarkuar...</div>

    return (
        <div className="p-6 lg:p-10 max-w-6xl mx-auto w-full pb-32">
            {/* Header Actions */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/invoices')}
                        className="p-2.5 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-800 hover:border-slate-300 transition-all shadow-sm"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-slate-800">
                            {isEdit ? 'Redakto Faturën' : 'Krijo Faturë të Re'}
                        </h1>
                        <p className="text-sm text-slate-400 font-medium">Plotësoni detajet e faturës më poshtë</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => handleSave('save')}
                        disabled={saving}
                        className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 text-white rounded-xl text-sm font-bold hover:bg-slate-900 transition-all shadow-lg shadow-slate-200 disabled:opacity-50"
                    >
                        <Save size={18} />
                        <span>Ruaj</span>
                    </button>
                    <button
                        onClick={() => handleSave('pdf')}
                        disabled={saving}
                        className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 disabled:opacity-50"
                    >
                        <FileDown size={18} />
                        <span>Ruaj & PDF</span>
                    </button>
                    <button
                        onClick={() => handleSave('email')}
                        disabled={saving}
                        className="flex items-center gap-2 px-5 py-2.5 bg-green-500 text-white rounded-xl text-sm font-bold hover:bg-green-600 transition-all shadow-lg shadow-green-200 disabled:opacity-50"
                    >
                        <Mail size={18} />
                        <span>Ruaj & Email</span>
                    </button>
                </div>
            </div>

            {/* Form Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column - Main Info */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Client Selection */}
                    <div className="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-sm relative">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold text-slate-800 flex items-center gap-2">
                                <Users size={18} className="text-blue-500" />
                                Informacioni i Klientit
                            </h3>
                            <button className="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1">
                                <UserPlus size={14} />
                                Klient i Ri
                            </button>
                        </div>

                        <div className="relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="text"
                                placeholder="Kërko klientin sipas emrit ose numrit unik..."
                                value={searchTerm || invoice.client_name}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value)
                                    setShowSuggestions(true)
                                }}
                                onFocus={() => setShowSuggestions(true)}
                                className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-12 pr-4 text-sm focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all transition-all"
                            />

                            <AnimatePresence>
                                {showSuggestions && searchTerm && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-2xl shadow-2xl z-50 max-h-64 overflow-auto overflow-hidden border-slate-100"
                                    >
                                        {filteredClients.map(client => (
                                            <div
                                                key={client.id}
                                                onClick={() => {
                                                    setInvoice(prev => ({ ...prev, client_id: client.id, client_name: client.name }))
                                                    setSearchTerm(client.name)
                                                    setShowSuggestions(false)
                                                }}
                                                className="p-4 hover:bg-blue-50 cursor-pointer flex items-center justify-between group border-b border-slate-50 last:border-0"
                                            >
                                                <div>
                                                    <p className="text-sm font-bold text-slate-800 group-hover:text-blue-700">{client.name}</p>
                                                    <p className="text-xs text-slate-400">{client.unique_number}</p>
                                                </div>
                                                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-blue-100 group-hover:text-blue-600">
                                                    <Plus size={16} />
                                                </div>
                                            </div>
                                        ))}
                                        {filteredClients.length === 0 && (
                                            <div className="p-8 text-center text-slate-400 text-sm">
                                                Nuk u gjet asnjë klient me këtë emër.
                                            </div>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {isOffer && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="mt-6 pt-6 border-t border-slate-100"
                            >
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 block">Subjekti i Ofertës</label>
                                <input
                                    type="text"
                                    placeholder="Psh: Instalimi i rrjetit elektrik..."
                                    value={invoice.subject}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, subject: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </motion.div>
                        )}
                    </div>

                    {/* Items Table */}
                    <div className="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-sm">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold text-slate-800 flex items-center gap-2">
                                <Plus size={18} className="text-blue-500" />
                                Artikujt e Faturës
                            </h3>
                            <button
                                onClick={addItemRow}
                                className="px-4 py-2 bg-slate-100 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-200 transition-all flex items-center gap-2"
                            >
                                <Plus size={14} />
                                Shto Rresht
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* Header */}
                            <div className="grid grid-cols-12 gap-4 px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest bg-slate-50/50 py-2 rounded-lg">
                                <div className="col-span-5">Përshkrimi</div>
                                <div className="col-span-2 text-center">Njësia</div>
                                <div className="col-span-1 text-center">Sasia</div>
                                <div className="col-span-2 text-center">Çmimi</div>
                                <div className="col-span-2 text-right">Totali</div>
                            </div>

                            {/* Rows */}
                            <div className="space-y-3">
                                {invoice.items.map((item, index) => (
                                    <motion.div
                                        key={index}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="grid grid-cols-12 gap-4 items-center group bg-white border border-slate-100 p-3 rounded-2xl hover:border-slate-200 transition-all"
                                    >
                                        <div className="col-span-5">
                                            <input
                                                type="text"
                                                placeholder="Emri i produktit ose shërbimit..."
                                                value={item.description}
                                                onChange={(e) => updateItem(index, 'description', e.target.value)}
                                                className="w-full bg-transparent border-none p-0 text-sm font-medium focus:ring-0 placeholder:text-slate-300"
                                            />
                                        </div>
                                        <div className="col-span-2">
                                            <input
                                                type="text"
                                                placeholder="Psh: Copa, M, L..."
                                                value={item.unit}
                                                onChange={(e) => updateItem(index, 'unit', e.target.value)}
                                                className="w-full bg-slate-50 border border-slate-100 rounded-xl py-2 text-center text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all uppercase"
                                            />
                                        </div>
                                        <div className="col-span-1">
                                            <input
                                                type="number"
                                                value={item.quantity}
                                                onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value) || 0)}
                                                className="w-full bg-slate-50 border border-slate-100 rounded-xl py-2 text-center text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                            />
                                        </div>
                                        <div className="col-span-2">
                                            <div className="relative">
                                                <input
                                                    type="number"
                                                    value={item.unit_price}
                                                    onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                                                    className="w-full bg-slate-50 border border-slate-100 rounded-xl py-2 pl-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                                />
                                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 font-bold">€</span>
                                            </div>
                                        </div>
                                        <div className="col-span-2 flex items-center justify-end gap-3">
                                            <span className="text-sm font-black text-slate-700">
                                                {(item.quantity * item.unit_price).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                            </span>
                                            <button
                                                onClick={() => removeItemRow(index)}
                                                className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column - Financial Summary */}
                <div className="space-y-8">
                    {/* Invoice Details */}
                    <div className="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-sm">
                        <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                            {isOffer ? <Briefcase size={18} className="text-blue-500" /> : <FileDown size={18} className="text-blue-500" />}
                            Detajet e {isOffer ? 'Ofertës' : 'Faturës'}
                        </h3>
                        <div className="space-y-5">
                            <div>
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 block">Numri i {isOffer ? 'Ofertës' : 'Faturës'}</label>
                                <input
                                    type="text"
                                    value={isOffer ? invoice.offer_number : invoice.invoice_number}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, [isOffer ? 'offer_number' : 'invoice_number']: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 block">Data e Lëshimit</label>
                                <input
                                    type="date"
                                    value={invoice.date}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, date: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 block">Afati i Pagesës</label>
                                <input
                                    type="date"
                                    value={invoice.payment_due_date}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, payment_due_date: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Totals */}
                    <div className="bg-slate-900 text-white p-8 rounded-3xl shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/10 blur-3xl -mr-16 -mt-16"></div>
                        <div className="absolute bottom-0 left-0 w-32 h-32 bg-blue-600/10 blur-3xl -ml-16 -mb-16"></div>

                        <div className="relative z-10 space-y-6">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-400">Nëntotali</span>
                                <span className="text-lg font-bold">{subtotal.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-slate-400">TVSH</span>
                                    <input
                                        type="number"
                                        value={invoice.vat_percentage}
                                        onChange={(e) => setInvoice(prev => ({ ...prev, vat_percentage: parseFloat(e.target.value) || 0 }))}
                                        className="w-12 bg-white/10 border-none rounded-lg text-center py-1 text-xs font-bold focus:ring-2 focus:ring-blue-500"
                                    />
                                    <span className="text-xs text-slate-500 font-bold">%</span>
                                </div>
                                <span className="text-lg font-bold">{vatAmount.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                            </div>

                            <div className="h-[1px] bg-white/10 my-6"></div>

                            <div className="flex items-end justify-between">
                                <div>
                                    <p className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-1">Total Për Pagesë</p>
                                    <p className="text-4xl font-black tracking-tighter">
                                        {total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                    </p>
                                </div>
                                <div className="p-3 bg-blue-600 rounded-2xl shadow-lg shadow-blue-500/20 group-hover:scale-110 transition-transform">
                                    <Calculator size={24} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default InvoiceForm
