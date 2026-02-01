import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import {
    Save,
    FileDown,
    Mail,
    Plus,
    Trash2,
    ArrowLeft,
    Search,
    X,
    UserPlus,
    Users
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { InvoiceService, OfferService, ClientService } from '../services/api'
import EmailPicker from '../components/EmailPicker'

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
    const [searchParams] = useSearchParams()

    const isOffer = location.pathname.startsWith('/offers')
    const service = isOffer ? OfferService : InvoiceService
    const cloneId = searchParams.get('clone')
    const isEdit = !!id
    const isClone = !!cloneId && !isEdit && !isOffer

    const [clients, setClients] = useState<any[]>([])
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [emailModalOpen, setEmailModalOpen] = useState(false)
    const [showZeroFields, setShowZeroFields] = useState<{ quantity: Record<number, boolean>; price: Record<number, boolean> }>({
        quantity: {},
        price: {}
    })
    const [priceDrafts, setPriceDrafts] = useState<Record<number, string>>({})
    const [vatEnabled, setVatEnabled] = useState(true)
    const [lastVatPercentage, setLastVatPercentage] = useState(18)
    const [useNumericPad, setUseNumericPad] = useState(() => {
        try {
            const savedPreference = localStorage.getItem('holkos_use_numeric_pad')
            if (savedPreference === '0') return false
            if (savedPreference === '1') return true
        } catch {
            // Ignore localStorage access errors.
        }
        return true
    })

    const [invoice, setInvoice] = useState<{
        invoice_number: string,
        offer_number: string,
        subject: string,
        description: string,
        date: string,
        payment_due_date: string,
        client_id: number | string,
        client_name: string,
        vat_percentage: number,
        items: InvoiceItem[]
    }>({
        invoice_number: '',
        offer_number: '',
        subject: '',
        description: '',
        date: new Date().toISOString().split('T')[0],
        payment_due_date: '',
        client_id: 0,
        client_name: '',
        vat_percentage: 18,
        items: [{ description: '', quantity: 0, unit_price: 0 }] as InvoiceItem[]
    })

    useEffect(() => {
        try {
            localStorage.setItem('holkos_use_numeric_pad', useNumericPad ? '1' : '0')
        } catch {
            // Ignore localStorage access errors.
        }
    }, [useNumericPad])

    useEffect(() => {
        ClientService.getAll().then(data => setClients(data))

        if (isEdit) {
            setLoading(true)
            service.getOne(parseInt(id))
                .then(data => {
                    const clientName = data.client?.name || ''
                    setInvoice({
                        ...data,
                        client_name: clientName
                    })
                    setVatEnabled((data.vat_percentage ?? 0) !== 0)
                    setLastVatPercentage(data.vat_percentage || 18)
                    setSearchTerm(clientName)
                })
                .finally(() => setLoading(false))
        } else if (isClone && cloneId) {
            setLoading(true)
            InvoiceService.getOne(parseInt(cloneId))
                .then(async data => {
                    const next = await InvoiceService.getNextNumber()
                    const clientName = data.client?.name || ''
                    setInvoice({
                        ...data,
                        id: undefined,
                        invoice_number: next.next_number,
                        date: new Date().toISOString().split('T')[0],
                        payment_due_date: '',
                        client_name: clientName
                    })
                    setVatEnabled((data.vat_percentage ?? 0) !== 0)
                    setLastVatPercentage(data.vat_percentage || 18)
                    setSearchTerm(clientName)
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
    }, [id, isEdit, isOffer, service, isClone, cloneId])

    const calculateSubtotal = () => {
        return invoice.items.reduce((acc, item) => acc + (item.quantity * item.unit_price), 0)
    }

    const subtotal = calculateSubtotal()
    const vatAmount = Number((subtotal * (invoice.vat_percentage / 100)).toFixed(2))
    const total = Number((subtotal + vatAmount).toFixed(2))

    const addItemRow = () => {
        setInvoice(prev => ({
            ...prev,
            items: [...prev.items, { description: '', quantity: 0, unit_price: 0 }]
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

    const setPriceDraft = (index: number, value: string) => {
        setPriceDrafts(prev => ({ ...prev, [index]: value }))
    }

    const dividePriceByVat = (index: number) => {
        const current = Number(invoice.items[index]?.unit_price || 0)
        const nextValue = Number((current / 1.18).toFixed(4))
        updateItem(index, 'unit_price', nextValue)
        setPriceDraft(index, nextValue === 0 ? '' : nextValue.toFixed(4))
        setShowZeroFields(prev => ({
            ...prev,
            price: { ...prev.price, [index]: nextValue !== 0 }
        }))
    }

    const handleSave = async (action: 'save' | 'pdf' | 'email', destEmail?: string) => {
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
            const isMobile = window.matchMedia('(max-width: 768px)').matches
            // Remove client_name from data as it's not part of the schema
            const { client_name, ...invoiceData } = invoice
            const data = {
                ...invoiceData,
                // If it's a temp ID (string), pass it as is. Offline interceptor will handle it.
                // If synced later, Sync Service must handle ID resolution (Client First, then Invoice).
                client_id: invoice.client_id,
                payment_due_date: invoice.payment_due_date || null,
                items: invoice.items.map(item => ({
                    ...item,
                    subtotal: item.quantity * item.unit_price
                })),
                subtotal,
                vat_amount: vatAmount,
                total,
                save_timestamp: new Date().toISOString()
            }
            let savedDoc;
            if (isEdit) {
                savedDoc = await service.update(parseInt(id!), data)
            } else {
                savedDoc = await service.create(data)
            }

            if (action === 'pdf') {
                const pdfEndpoint = isOffer ? `/api/offers/${savedDoc.id}/pdf` : `/api/invoices/${savedDoc.id}/pdf`
                if (isMobile) {
                    window.location.href = pdfEndpoint
                    return
                } else {
                    window.open(pdfEndpoint, '_blank')
                }
            } else if (action === 'email') {
                if (!destEmail) {
                    alert('Ju lutem zgjidhni një email!')
                    return
                }
                await service.email(savedDoc.id, destEmail)
                alert('Email-i u dërgua me sukses!')
            }

            navigate(isOffer ? '/offers' : '/invoices')
        } catch (error: any) {
            console.error('Error saving invoice:', error)
            console.error('Error response:', error.response?.data)
            const detail = error.response?.data?.detail || error.message || 'Gabim gjatë ruajtjes!'
            alert(detail)
        } finally {
            setSaving(false)
        }
    }

    const filteredClients = clients.filter(c =>
        (String(c?.name ?? '')).toLowerCase().includes((searchTerm || '').toLowerCase()) ||
        (String(c?.unique_number ?? '')).toLowerCase().includes((searchTerm || '').toLowerCase())
    )

    const selectedClientEmail = clients.find(c => c.id === invoice.client_id)?.email || ''

    if (loading) return <div className="p-8 text-center text-gray-500">Duke u ngarkuar...</div>

    return (
        <div className="p-4 sm:p-6 lg:p-10 max-w-6xl mx-auto w-full pb-32">
            {/* Header Actions */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
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

                <div />
            </div>

            {/* Form Content */}
            <div className="space-y-8">
                {/* Info Card - Combined Client & Doc Details */}
                <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-6">
                    <div className="flex flex-col lg:flex-row lg:items-end gap-6">
                        {/* Client Selection */}
                        <div className="relative space-y-3 lg:w-[45%]">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                                    <Users size={18} className="text-blue-500" />
                                    Informacioni i Klientit
                                </h3>
                                <button
                                    type="button"
                                    onClick={() => navigate('/clients')}
                                    className="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1"
                                >
                                    <UserPlus size={14} />
                                    Klient i Ri
                                </button>
                            </div>

                            <div className="relative">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Kërko klientin sipas emrit ose numrit unik..."
                                    value={searchTerm}
                                    onChange={(e) => {
                                        const value = e.target.value
                                        setSearchTerm(value)
                                        setShowSuggestions(true)
                                        if (!value) {
                                            setInvoice(prev => ({ ...prev, client_id: 0, client_name: '' }))
                                            return
                                        }
                                        const match = clients.find((c) => {
                                            const label = `${c.name}${c.unique_number ? ` (${c.unique_number})` : ''}`
                                            return label.toLowerCase() === value.toLowerCase()
                                        })
                                        if (match) {
                                            setInvoice(prev => ({ ...prev, client_id: match.id, client_name: match.name }))
                                        }
                                    }}
                                    onFocus={() => setShowSuggestions(true)}
                                    onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 pl-12 pr-12 text-[16px] sm:text-sm focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowSuggestions(prev => !prev)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white border border-slate-200 text-slate-400 flex items-center justify-center hover:bg-slate-50"
                                >
                                    ▼
                                </button>

                                <AnimatePresence>
                                    {showSuggestions && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 6 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 6 }}
                                            className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-2xl shadow-2xl z-50 max-h-64 overflow-auto"
                                        >
                                            {filteredClients.length === 0 ? (
                                                <div className="px-4 py-3 text-sm text-slate-400">Nuk u gjet asnjë klient</div>
                                            ) : (
                                                filteredClients.map(client => (
                                                    <div
                                                        key={client.id}
                                                        onMouseDown={() => {
                                                            setInvoice(prev => ({ ...prev, client_id: client.id, client_name: client.name }))
                                                            setSearchTerm(client.name)
                                                            setShowSuggestions(false)
                                                        }}
                                                        className="px-4 py-3 hover:bg-blue-50 cursor-pointer border-b border-slate-50 last:border-0"
                                                    >
                                                        <div className="text-sm font-bold text-slate-800">{client.name}</div>
                                                        <div className="text-xs text-slate-400">{client.unique_number}</div>
                                                    </div>
                                                ))
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Doc Details Grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-1 lg:pt-0 lg:w-[55%] min-w-0">
                            <div className="min-w-0">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Numri i {isOffer ? 'Ofertës' : 'Faturës'}</label>
                                <input
                                    type="text"
                                    value={isOffer ? invoice.offer_number : invoice.invoice_number}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, [isOffer ? 'offer_number' : 'invoice_number']: e.target.value }))}
                                    className="w-full min-w-0 bg-slate-50 border border-slate-100 rounded-xl py-2.5 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                            <div className="min-w-0">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Data e Lëshimit</label>
                                <input
                                    type="date"
                                    value={invoice.date}
                                    onChange={(e) => setInvoice(prev => ({ ...prev, date: e.target.value }))}
                                    className="w-full min-w-0 max-w-full bg-slate-50 border border-slate-100 rounded-xl h-10 px-3 text-[13px] font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none"
                                />
                            </div>
                            <div className="min-w-0">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Afati i Pagesës</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={invoice.payment_due_date}
                                        onChange={(e) => setInvoice(prev => ({ ...prev, payment_due_date: e.target.value }))}
                                        className="w-full min-w-0 max-w-full bg-slate-50 border border-slate-100 rounded-xl h-10 px-3 pr-10 text-[13px] font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none"
                                    />
                                    {invoice.payment_due_date && (
                                        <button
                                            type="button"
                                            onClick={() => setInvoice(prev => ({ ...prev, payment_due_date: '' }))}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-200 rounded-full transition-colors"
                                            title="Reset"
                                        >
                                            <X size={14} className="text-slate-500" />
                                        </button>
                                    )}
                                </div>
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
                <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/60 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-bold text-slate-800 flex items-center gap-2">

                            Artikujt e {isOffer ? 'Ofertës' : 'Faturës'}
                        </h3>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => {
                                    setUseNumericPad(prev => !prev)
                                }}
                                className="px-3 py-2 bg-white text-slate-600 rounded-xl text-[11px] font-bold border border-slate-200 hover:bg-slate-50 transition-all"
                            >
                                {useNumericPad ? 'ABC' : '123'}
                            </button>
                            <button
                                onClick={addItemRow}
                                className="w-full sm:w-auto px-5 py-2 bg-slate-50 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-100 transition-all flex items-center justify-center gap-2 border border-slate-200"
                            >
                                <Plus size={14} />
                                Shto Rresht
                            </button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {/* Table Header (desktop only) */}
                        <div className="hidden sm:grid grid-cols-12 gap-4 px-4 text-[10px] font-black text-slate-400 uppercase tracking-widest bg-slate-50 py-2 rounded-lg">
                            <div className="col-span-6">Përshkrimi</div>
                            <div className="col-span-2 text-center">Sasia</div>
                            <div className="col-span-2 text-center">Çmimi</div>
                            <div className="col-span-2 text-right">Totali</div>
                        </div>

                        {/* Rows */}
                        <div className="space-y-2">
                            {invoice.items.map((item, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 6 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="group bg-white border border-slate-100 p-3 rounded-xl overflow-hidden"
                                >
                                    <div className="flex flex-col gap-2 sm:grid sm:grid-cols-12 sm:gap-3 sm:items-center min-w-0">
                                        <div className="sm:col-span-6 min-w-0">
                                            <label className="sm:hidden text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block">Përshkrimi</label>
                                            <input
                                                type="text"
                                                placeholder="Përshkrimi i artikullit..."
                                                value={item.description}
                                                onChange={(e) => updateItem(index, 'description', e.target.value)}
                                                className="w-full max-w-full bg-slate-50 border border-slate-100 rounded-lg px-3 py-1.5 text-[16px] sm:text-sm font-semibold text-slate-700 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all placeholder:text-slate-300"
                                            />
                                        </div>
                                        <div className="sm:col-span-2 min-w-0">
                                            <label className="sm:hidden text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block">Sasia</label>
                                            <div className="relative">
                                                <input
                                                    id={`num-input-quantity-${index}`}
                                                    type={useNumericPad ? 'number' : 'text'}
                                                    inputMode={useNumericPad ? 'decimal' : 'text'}
                                                    pattern={useNumericPad ? '[0-9]*' : undefined}
                                                    value={useNumericPad
                                                        ? (item.quantity === 0 ? (showZeroFields.quantity[index] ? 0 : '') : item.quantity)
                                                        : (item.quantity === 0 ? '' : String(item.quantity))}
                                                    onChange={(e) => {
                                                        const value = e.target.value
                                                        setShowZeroFields(prev => ({
                                                            ...prev,
                                                            quantity: { ...prev.quantity, [index]: value !== '' }
                                                        }))
                                                        updateItem(index, 'quantity', value === '' ? 0 : parseFloat(value) || 0)
                                                    }}
                                                    className="w-full max-w-full bg-slate-50 border border-slate-100 rounded-lg py-1.5 pr-7 text-right text-[16px] sm:text-sm font-bold focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all"
                                                />
                                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 font-bold">m2</span>
                                            </div>
                                        </div>
                                        <div className="sm:col-span-2 min-w-0">
                                            <label className="sm:hidden text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block">Çmimi</label>
                                            <div className="relative">
                                                <input
                                                    id={`num-input-price-${index}`}
                                                    type={useNumericPad ? 'number' : 'text'}
                                                    inputMode={useNumericPad ? 'decimal' : 'text'}
                                                    pattern={useNumericPad ? '[0-9]*' : undefined}
                                                    value={useNumericPad
                                                        ? (priceDrafts[index] ?? (item.unit_price === 0 ? '' : String(item.unit_price)))
                                                        : (priceDrafts[index] ?? (item.unit_price === 0 ? '' : String(item.unit_price)))}
                                                    onChange={(e) => {
                                                        const value = e.target.value
                                                        setPriceDraft(index, value)
                                                        setShowZeroFields(prev => ({
                                                            ...prev,
                                                            price: { ...prev.price, [index]: value !== '' }
                                                        }))
                                                        updateItem(index, 'unit_price', value === '' ? 0 : parseFloat(value) || 0)
                                                    }}
                                                    onBlur={() => {
                                                        const raw = priceDrafts[index]
                                                        if (raw !== undefined) {
                                                            const parsed = raw === '' ? 0 : parseFloat(raw) || 0
                                                            updateItem(index, 'unit_price', parsed)
                                                        }
                                                    }}
                                                    className="w-full max-w-full bg-slate-50 border border-slate-100 rounded-lg py-1.5 pr-24 text-right text-[16px] sm:text-sm font-bold focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:bg-white transition-all"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => dividePriceByVat(index)}
                                                    className="absolute right-9 top-1/2 -translate-y-1/2 text-[10px] font-bold text-blue-600 bg-blue-50 border border-blue-100 rounded-md px-2 py-0.5 hover:bg-blue-100"
                                                    title="Përjashto TVSH (÷1.18)"
                                                >
                                                    ÷1.18
                                                </button>
                                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 font-bold">€</span>
                                            </div>
                                        </div>
                                        <div className="sm:col-span-2 flex items-center justify-between sm:justify-end gap-4">
                                            <div>
                                                <label className="sm:hidden text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block">Totali</label>
                                                <span className="text-sm font-black text-slate-800">
                                                    {(item.quantity * item.unit_price).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                                </span>
                                            </div>
                                            <button
                                                onClick={() => removeItemRow(index)}
                                                className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all sm:opacity-0 sm:group-hover:opacity-100"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>

                    {/* Compact Totals */}
                    <div className="mt-3 grid grid-cols-1 gap-2 max-w-xs ml-auto">
                        <div className="border border-slate-200 rounded-lg px-3 py-2 flex items-center justify-between">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Nëntotali</span>
                            <span className="text-xs font-bold text-slate-900">{subtotal.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                        </div>
                        <div className="border border-slate-200 rounded-lg px-3 py-2 flex items-center justify-between gap-2">
                            <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                <input
                                    type="checkbox"
                                    checked={vatEnabled}
                                    onChange={(e) => {
                                        const checked = e.target.checked
                                        setVatEnabled(checked)
                                        if (!checked) {
                                            setLastVatPercentage(prev => invoice.vat_percentage || prev || 18)
                                            setInvoice(prev => ({ ...prev, vat_percentage: 0 }))
                                            return
                                        }
                                        setInvoice(prev => ({ ...prev, vat_percentage: lastVatPercentage || 18 }))
                                    }}
                                    className="h-3.5 w-3.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500/30"
                                />
                                TVSH
                            </label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="number"
                                    value={invoice.vat_percentage}
                                    onChange={(e) => {
                                        const value = parseFloat(e.target.value) || 0
                                        setInvoice(prev => ({ ...prev, vat_percentage: value }))
                                        setLastVatPercentage(value || lastVatPercentage)
                                    }}
                                    disabled={!vatEnabled}
                                    className={`w-14 bg-slate-50 border border-slate-200 rounded-md text-center py-0.5 text-[11px] font-bold focus:ring-2 focus:ring-blue-500/30 focus:bg-white ${vatEnabled ? '' : 'opacity-50 cursor-not-allowed'}`}
                                />
                                <span className="text-[11px] font-semibold text-slate-500">{vatAmount.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                            </div>
                        </div>
                        <div className="border border-slate-900 bg-slate-900 text-white rounded-lg px-3 py-2 flex items-center justify-between">
                            <span className="text-[10px] font-black uppercase tracking-widest text-white/70">Për Pagesë</span>
                            <span className="text-xs font-black">{total.toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €</span>
                        </div>
                    </div>

                </div>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch gap-3 bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/60 shadow-sm">
                    <button
                        onClick={() => handleSave('save')}
                        disabled={saving}
                        className="w-full sm:flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-slate-800 text-white rounded-2xl text-sm font-black hover:bg-slate-900 transition-all shadow-lg shadow-slate-200 disabled:opacity-50"
                    >
                        <Save size={20} />
                        <span>RUAJ</span>
                    </button>
                    <button
                        onClick={() => handleSave('pdf')}
                        disabled={saving}
                        className="w-full sm:flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-orange-600 text-white rounded-2xl text-sm font-black hover:bg-orange-700 transition-all shadow-lg shadow-orange-200 disabled:opacity-50"
                    >
                        <FileDown size={20} />
                        <span>RUAJ & PDF</span>
                    </button>
                    <button
                        onClick={() => setEmailModalOpen(true)}
                        disabled={saving}
                        className="w-full sm:flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-green-600 text-white rounded-2xl text-sm font-black hover:bg-green-700 transition-all shadow-lg shadow-green-200 disabled:opacity-50"
                    >
                        <Mail size={20} />
                        <span>RUAJ & EMAIL</span>
                    </button>
                </div>
            </div>

            <EmailPicker
                isOpen={emailModalOpen}
                title="Dërgo faturën me email"
                initialEmail={selectedClientEmail}
                onClose={() => setEmailModalOpen(false)}
                onConfirm={(email) => {
                    setEmailModalOpen(false)
                    handleSave('email', email)
                }}
            />
        </div>
    )
}

export default InvoiceForm
