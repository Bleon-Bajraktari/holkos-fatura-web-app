import { useState, useEffect } from 'react'
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
    Users
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { InvoiceService, OfferService, ClientService } from '../services/api'

interface InvoiceItem {
    id?: number
    description: string
    quantity: number
    unit_price: number
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
        items: [{ description: '', quantity: 1, unit_price: 0 }] as InvoiceItem[]
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
            const fetchNext = async () => {
                try {
                    const data = isOffer ? await OfferService.getNextNumber() : await InvoiceService.getNextNumber()
                    setInvoice(prev => ({ ...prev, [isOffer ? 'offer_number' : 'invoice_number']: data.next_number }))
                } catch (err) {
                    console.error('Error fetching next number:', err)
                }
            }
            fetchNext()
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
                payment_due_date: invoice.payment_due_date || null,
                items: invoice.items.map(item => ({
                    ...item,
                    subtotal: item.quantity * item.unit_price
                })),
                subtotal,
                vat_amount: vatAmount,
                total
            }
            let savedDoc;
            if (isEdit) {
                savedDoc = await service.update(parseInt(id!), data)
            } else {
                savedDoc = await service.create(data)
            }

            if (action === 'pdf') {
                const pdfEndpoint = isOffer ? `/api/offers/${savedDoc.id}/pdf` : `/api/invoices/${savedDoc.id}/pdf`
                window.open(pdfEndpoint, '_blank')
            } else if (action === 'email') {
                await service.email(savedDoc.id)
                alert('Email-i u dërgua me sukses!')
            }

            navigate(isOffer ? '/offers' : '/invoices')
        } catch (error: any) {
            console.error('Error saving:', error)
            const detail = error.response?.data?.detail || 'Gabim gjatë ruajtjes!'
            alert(detail)
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
                    {isEdit && (
                        <button
                            onClick={() => {
                                setInvoice(prev => ({
                                    ...prev,
                                    [isOffer ? 'offer_number' : 'invoice_number']: 'KOPJE-' + (isOffer ? prev.offer_number : prev.invoice_number),
                                    date: new Date().toISOString().split('T')[0]
                                }))
                                navigate(isOffer ? '/offers/new' : '/invoices/new')
                            }}
                            className="flex items-center gap-2 px-5 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-bold hover:bg-amber-600 transition-all shadow-lg shadow-amber-200"
                        >
                            <Copy size={18} />
                            <span>Klono</span>
                        </button>
                    )}
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
            <div className="space-y-8">
                {/* Info Card - Combined Client & Doc Details */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-8">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Client Selection */}
                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
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
                                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-12 pr-4 text-sm focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all"
                                />

                                <AnimatePresence>
                                    {showSuggestions && searchTerm && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0 }}
                                            className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-2xl shadow-2xl z-50 max-h-64 overflow-auto overflow-hidden"
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
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Doc Details Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-1">
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Numri i {isOffer ? 'Ofertës' : 'Faturës'}</label>
                                <input
                                    type="text"
                                    value={isOffer ? invoice.offer_number : invoice.invoice_number}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, [isOffer ? 'offer_number' : 'invoice_number']: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Data e Lëshimit</label>
                                <input
                                    type="date"
                                    value={invoice.date}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, date: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Afati i Pagesës</label>
                                <input
                                    type="date"
                                    value={invoice.payment_due_date}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, payment_due_date: e.target.value }))}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>
                    </div>

                    {isOffer && (
                        <div className="pt-6 border-t border-slate-100">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Subjekti i Ofertës</label>
                            <input
                                type="text"
                                placeholder="Psh: Instalimi i rrjetit elektrik..."
                                value={invoice.subject}
                                onChange={(e) => setInvoice(prev => ({ ...prev, subject: e.target.value }))}
                                className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                    )}
                </div>

                {/* Items Table */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="font-bold text-slate-800 flex items-center gap-2">
                            <Plus size={18} className="text-blue-500" />
                            Artikujt e {isOffer ? 'Ofertës' : 'Faturës'}
                        </h3>
                        <button
                            onClick={addItemRow}
                            className="px-6 py-2.5 bg-blue-50 text-blue-600 rounded-xl text-xs font-bold hover:bg-blue-100 transition-all flex items-center gap-2 border border-blue-100"
                        >
                            <Plus size={14} />
                            Shto Rresht
                        </button>
                    </div>

                    <div className="space-y-4">
                        {/* Table Header */}
                        <div className="grid grid-cols-12 gap-6 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest bg-slate-50/50 py-3 rounded-xl">
                            <div className="col-span-7">Përshkrimi</div>
                            <div className="col-span-1 text-center">Sasia (M²)</div>
                            <div className="col-span-2 text-center">Çmimi</div>
                            <div className="col-span-2 text-right">Totali</div>
                        </div>

                        {/* Rows */}
                        <div className="space-y-3">
                            {invoice.items.map((item, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="grid grid-cols-12 gap-6 items-center group bg-white border border-slate-100 p-4 rounded-2xl hover:border-blue-200 hover:shadow-md hover:shadow-blue-500/5 transition-all"
                                >
                                    <div className="col-span-7">
                                        <input
                                            type="text"
                                            placeholder="Përshkrimi i artikullit..."
                                            value={item.description}
                                            onChange={(e) => updateItem(index, 'description', e.target.value)}
                                            className="w-full bg-transparent border-none p-0 text-sm font-bold text-slate-700 focus:ring-0 placeholder:text-slate-300"
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
                                    <div className="col-span-2 flex items-center justify-end gap-4">
                                        <span className="text-sm font-black text-slate-800">
                                            {(item.quantity * item.unit_price).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                        </span>
                                        <button
                                            onClick={() => removeItemRow(index)}
                                            className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Bottom Section - Totals & Actions */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-end">
                    {/* Actions - Left Bottom */}
                    <div className="flex flex-wrap items-center gap-4 bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm">
                        <button
                            onClick={() => handleSave('save')}
                            disabled={saving}
                            className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-slate-800 text-white rounded-2xl text-sm font-black hover:bg-slate-900 transition-all shadow-lg shadow-slate-200 disabled:opacity-50"
                        >
                            <Save size={20} />
                            <span>RUAU</span>
                        </button>
                        <button
                            onClick={() => handleSave('pdf')}
                            disabled={saving}
                            className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-orange-600 text-white rounded-2xl text-sm font-black hover:bg-orange-700 transition-all shadow-lg shadow-orange-200 disabled:opacity-50"
                        >
                            <FileDown size={20} />
                            <span>RUAJ & PDF</span>
                        </button>
                        <button
                            onClick={() => handleSave('email')}
                            disabled={saving}
                            className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-green-600 text-white rounded-2xl text-sm font-black hover:bg-green-700 transition-all shadow-lg shadow-green-200 disabled:opacity-50"
                        >
                            <Mail size={20} />
                            <span>RUAJ & EMAIL</span>
                        </button>
                    </div>

                    {/* Totals - Right Bottom */}
                    <div className="bg-slate-900 text-white p-10 rounded-3xl shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-[100px] -mr-32 -mt-32"></div>
                        <div className="relative z-10 space-y-8">
                            <div className="grid grid-cols-2 gap-8">
                                <div className="space-y-1">
                                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Nëntotali</p>
                                    <p className="text-xl font-bold">{subtotal.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</p>
                                </div>
                                <div className="space-y-1 text-right">
                                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">TVSH (%):</p>
                                    <div className="flex items-center justify-end gap-2">
                                        <input
                                            type="number"
                                            value={invoice.vat_percentage}
                                            onChange={(e) => setInvoice(prev => ({ ...prev, vat_percentage: parseFloat(e.target.value) || 0 }))}
                                            className="w-16 bg-white/5 border border-white/10 rounded-lg text-center py-1.5 text-sm font-black focus:ring-2 focus:ring-blue-500"
                                        />
                                        <span className="text-sm font-bold text-slate-400">{vatAmount.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                                    </div>
                                </div>
                            </div>

                            <div className="h-px bg-white/10"></div>

                            <div className="flex items-center justify-between">
                                <div className="space-y-1">
                                    <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Totali Për Pagesë</p>
                                    <p className="text-5xl font-black tracking-tighter">
                                        {total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                    </p>
                                </div>
                                <div className="w-16 h-16 bg-blue-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-blue-500/40 transform rotate-12">
                                    <Calculator size={32} />
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
