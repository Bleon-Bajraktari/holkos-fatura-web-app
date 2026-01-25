import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Save, FileDown, MoveUp, MoveDown, X, Eye, Search, UserPlus, Users } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { OfferService, ClientService } from '../services/api'

type OfferRowType = 'item' | 'header' | 'text'

interface OfferModule {
    id: string
    value: string
    unit: string
}

interface OfferRow {
    id: string
    row_type: OfferRowType
    description: string
    modules: OfferModule[]
    has_border: boolean
}

const createRow = (row_type: OfferRowType): OfferRow => ({
    id: `${Date.now()}-${Math.random()}`,
    row_type,
    description: '',
    modules: row_type === 'item'
        ? [
            { id: `${Date.now()}-price`, value: '', unit: '€' },
            { id: `${Date.now()}-qty`, value: '', unit: 'm²' }
        ]
        : [],
    has_border: true
})

const OfferForm = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const isEdit = !!id

    const [clients, setClients] = useState<any[]>([])
    const [searchTerm, setSearchTerm] = useState('')
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [fontSize, setFontSize] = useState('Auto')

    const [offer, setOffer] = useState({
        offer_number: '',
        subject: '',
        date: new Date().toISOString().split('T')[0],
        client_id: 0,
        client_name: ''
    })
    const [rows, setRows] = useState<OfferRow[]>([createRow('item')])

    useEffect(() => {
        ClientService.getAll().then(data => setClients(data))

        if (isEdit) {
            setLoading(true)
            OfferService.getOne(parseInt(id!))
                .then(data => {
                    setOffer({
                        offer_number: data.offer_number,
                        subject: data.subject || '',
                        date: data.date,
                        client_id: data.client_id,
                        client_name: data.client?.name || ''
                    })
                    const mappedRows: OfferRow[] = (data.items || []).map((item: any) => {
                        let custom = item.custom_attributes
                        if (typeof custom === 'string') {
                            try {
                                custom = JSON.parse(custom)
                            } catch {
                                custom = null
                            }
                        }
                        const modules = custom?.modules || []
                        return {
                            id: `${Date.now()}-${Math.random()}`,
                            row_type: item.row_type || 'item',
                            description: item.description || '',
                            modules: (modules || []).map((mod: any, idx: number) => ({
                                id: `${Date.now()}-${idx}-${Math.random()}`,
                                value: String(mod.value ?? ''),
                                unit: String(mod.unit ?? '')
                            })),
                            has_border: custom?.has_border ?? true
                        }
                    })
                    setRows(mappedRows.length > 0 ? mappedRows : [createRow('item')])
                })
                .finally(() => setLoading(false))
        } else {
            OfferService.getNextNumber().then(data => {
                setOffer(prev => ({ ...prev, offer_number: data.next_number }))
            })
        }
    }, [id, isEdit])

    const filteredClients = useMemo(() => {
        const term = searchTerm.toLowerCase()
        return clients.filter(c =>
            c.name.toLowerCase().includes(term) ||
            c.unique_number?.toLowerCase().includes(term)
        )
    }, [clients, searchTerm])

    const addRow = (type: OfferRowType) => {
        setRows(prev => [...prev, createRow(type)])
    }

    const removeRow = (rowId: string) => {
        setRows(prev => prev.filter(row => row.id !== rowId))
    }

    const moveRow = (rowId: string, direction: -1 | 1) => {
        setRows(prev => {
            const idx = prev.findIndex(r => r.id === rowId)
            if (idx === -1) return prev
            const newIdx = idx + direction
            if (newIdx < 0 || newIdx >= prev.length) return prev
            const copy = [...prev]
            const [moved] = copy.splice(idx, 1)
            copy.splice(newIdx, 0, moved)
            return copy
        })
    }

    const addModule = (rowId: string) => {
        setRows(prev => prev.map(row => {
            if (row.id !== rowId) return row
            return {
                ...row,
                modules: [...row.modules, { id: `${Date.now()}-${Math.random()}`, value: '', unit: '' }]
            }
        }))
    }

    const removeModule = (rowId: string, moduleId: string) => {
        setRows(prev => prev.map(row => {
            if (row.id !== rowId) return row
            return { ...row, modules: row.modules.filter(m => m.id !== moduleId) }
        }))
    }

    const updateRow = (rowId: string, patch: Partial<OfferRow>) => {
        setRows(prev => prev.map(row => row.id === rowId ? { ...row, ...patch } : row))
    }

    const updateModule = (rowId: string, moduleId: string, patch: Partial<OfferModule>) => {
        setRows(prev => prev.map(row => {
            if (row.id !== rowId) return row
            return {
                ...row,
                modules: row.modules.map(mod => mod.id === moduleId ? { ...mod, ...patch } : mod)
            }
        }))
    }

    const calculateRowSubtotal = (row: OfferRow) => {
        if (row.row_type !== 'item') return 0
        const nums = row.modules
            .map(m => parseFloat(String(m.value).replace(',', '.')))
            .filter(v => !Number.isNaN(v))
        if (nums.length === 0) return 0
        return nums.reduce((acc, v) => acc * v, 1)
    }

    const subtotal = rows.reduce((acc, row) => acc + calculateRowSubtotal(row), 0)

    const handlePreview = async () => {
        if (!offer.client_id) {
            alert('Ju lutem zgjidhni një klient!')
            return
        }
        if (!rows.length) {
            alert('Shto të paktën një rresht!')
            return
        }
        setSaving(true)
        try {
            const items = rows.map((row, idx) => {
                const rowSubtotal = calculateRowSubtotal(row)
                return {
                    description: row.description,
                    unit: '',
                    quantity: row.row_type === 'item' ? 1 : 0,
                    unit_price: row.row_type === 'item' ? rowSubtotal : 0,
                    subtotal: row.row_type === 'item' ? rowSubtotal : 0,
                    row_type: row.row_type,
                    order_index: idx,
                    custom_attributes: {
                        modules: row.modules.map(m => ({ value: m.value, unit: m.unit })),
                        has_border: row.has_border
                    }
                }
            })

            const payload = {
                offer_number: offer.offer_number,
                subject: offer.subject,
                date: offer.date,
                client_id: offer.client_id,
                subtotal,
                vat_percentage: 0,
                vat_amount: 0,
                total: subtotal,
                items
            }

            // Use preview endpoint that doesn't save to database
            const queryParam = fontSize && fontSize !== 'Auto' ? `?font_size=${fontSize}` : ''
            const isMobile = window.matchMedia('(max-width: 768px)').matches || /iPhone|iPad|iPod/i.test(navigator.userAgent)

            if (isMobile) {
                // For mobile devices (especially iOS), store data temporarily on server
                const previewId = `preview_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

                // First, store the data on server via POST
                const storeResponse = await fetch(`/api/offers/preview-store/${previewId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                })

                if (!storeResponse.ok) {
                    throw new Error('Gabim gjatë ruajtjes së të dhënave për preview!')
                }

                // Then navigate to GET endpoint (works better on iOS)
                window.location.href = `/api/offers/preview-pdf/${previewId}${queryParam}`
            } else {
                // For desktop, use fetch and blob
                const response = await fetch(`/api/offers/preview-pdf${queryParam}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                })

                if (!response.ok) {
                    const error = await response.json().catch(() => ({ detail: 'Gabim gjatë preview!' }))
                    throw new Error(error.detail || 'Gabim gjatë preview!')
                }

                // Get PDF blob and open it
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                window.open(url, '_blank')
                // Clean up the URL after a delay
                setTimeout(() => window.URL.revokeObjectURL(url), 100)
            }
        } catch (error: any) {
            console.error('Error previewing offer:', error)
            const detail = error.message || 'Gabim gjatë preview!'
            alert(detail)
        } finally {
            setSaving(false)
        }
    }

    const handleSave = async (action: 'save' | 'pdf') => {
        if (!offer.client_id) {
            alert('Ju lutem zgjidhni një klient!')
            return
        }
        if (!rows.length) {
            alert('Shto të paktën një rresht!')
            return
        }
        setSaving(true)
        try {
            const items = rows.map((row, idx) => {
                const rowSubtotal = calculateRowSubtotal(row)
                return {
                    description: row.description,
                    unit: '',
                    quantity: row.row_type === 'item' ? 1 : 0,
                    unit_price: row.row_type === 'item' ? rowSubtotal : 0,
                    subtotal: row.row_type === 'item' ? rowSubtotal : 0,
                    row_type: row.row_type,
                    order_index: idx,
                    custom_attributes: {
                        modules: row.modules.map(m => ({ value: m.value, unit: m.unit })),
                        has_border: row.has_border
                    }
                }
            })

            const payload = {
                offer_number: offer.offer_number,
                subject: offer.subject,
                date: offer.date,
                client_id: offer.client_id,
                subtotal,
                vat_percentage: 0,
                vat_amount: 0,
                total: subtotal,
                items
            }

            let saved
            if (isEdit) {
                saved = await OfferService.update(parseInt(id!), payload)
            } else {
                saved = await OfferService.create(payload)
            }

            if (action === 'pdf') {
                const pdfUrl = `/api/offers/${saved.id}/pdf${fontSize && fontSize !== 'Auto' ? `?font_size=${fontSize}` : ''}`
                window.open(pdfUrl, '_blank')
            }
            navigate('/offers')
        } catch (error: any) {
            console.error('Error saving offer:', error)
            const detail = error.response?.data?.detail || error.message || 'Gabim gjatë ruajtjes!'
            alert(detail)
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <div className="p-8 text-center text-gray-500">Duke u ngarkuar...</div>

    return (
        <div className="p-4 sm:p-6 lg:p-10 max-w-6xl mx-auto w-full pb-24">
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
                            {isEdit ? 'Redakto Ofertën' : 'Krijo Ofertë të Re'}
                        </h1>
                        <p className="text-sm text-slate-400 font-medium">Plotësoni detajet e ofertës më poshtë</p>
                    </div>
                </div>

                <div />
            </div>

            <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="relative space-y-3">
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
                                        setOffer(prev => ({ ...prev, client_id: 0, client_name: '' }))
                                        return
                                    }
                                    const match = clients.find((c) => {
                                        const label = `${c.name}${c.unique_number ? ` (${c.unique_number})` : ''}`
                                        return label.toLowerCase() === value.toLowerCase()
                                    })
                                    if (match) {
                                        setOffer(prev => ({ ...prev, client_id: match.id, client_name: match.name }))
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
                                                        setOffer(prev => ({ ...prev, client_id: client.id, client_name: client.name }))
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

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Numri i Ofertës</label>
                            <input
                                type="text"
                                value={offer.offer_number}
                                onChange={(e) => setOffer(prev => ({ ...prev, offer_number: e.target.value }))}
                                className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all"
                            />
                        </div>
                        <div className="min-w-0">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Data e Ofertës</label>
                            <input
                                type="date"
                                value={offer.date}
                                onChange={(e) => setOffer(prev => ({ ...prev, date: e.target.value }))}
                                className="w-full min-w-0 max-w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all appearance-none"
                            />
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Titulli / Subjekti</label>
                        <input
                            type="text"
                            value={offer.subject}
                            onChange={(e) => setOffer(prev => ({ ...prev, subject: e.target.value }))}
                            className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all"
                        />
                    </div>
                    <div>
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">Madhësia e Tekstit</label>
                        <select
                            value={fontSize}
                            onChange={(e) => setFontSize(e.target.value)}
                            className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/20 focus:bg-white transition-all"
                        >
                            <option value="Auto">Auto</option>
                            <option value="10">10</option>
                            <option value="11">11</option>
                            <option value="12">12</option>
                            <option value="13">13</option>
                            <option value="14">14</option>
                            <option value="15">15</option>
                            <option value="16">16</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="mt-6 bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest">Përshkrimi i Artikujve dhe Kalkulimet</h3>
                    <div className="flex flex-wrap items-center gap-2">
                        <button onClick={() => addRow('item')} className="w-full sm:w-auto px-4 py-2 bg-blue-50 text-blue-600 rounded-xl text-xs font-bold hover:bg-blue-100 transition-all">+ Artikull</button>
                        <button onClick={() => addRow('header')} className="w-full sm:w-auto px-4 py-2 bg-slate-50 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-100 transition-all">+ Titull</button>
                        <button onClick={() => addRow('text')} className="w-full sm:w-auto px-4 py-2 bg-purple-50 text-purple-600 rounded-xl text-xs font-bold hover:bg-purple-100 transition-all">+ Tekst</button>
                    </div>
                </div>

                <div className="space-y-4">
                    {rows.map((row) => (
                        <div key={row.id} className={`border ${row.has_border ? 'border-slate-200' : 'border-transparent'} rounded-2xl p-4`}>
                            <div className="flex items-start gap-3">
                                <div className="flex flex-col gap-2">
                                    <button onClick={() => moveRow(row.id, -1)} className="p-1 text-slate-400 hover:text-slate-700"><MoveUp size={16} /></button>
                                    <button onClick={() => moveRow(row.id, 1)} className="p-1 text-slate-400 hover:text-slate-700"><MoveDown size={16} /></button>
                                </div>

                                <div className="flex-1 space-y-3 min-w-0">
                                    {row.row_type === 'header' ? (
                                        <input
                                            type="text"
                                            value={row.description}
                                            onChange={(e) => updateRow(row.id, { description: e.target.value })}
                                            placeholder="TITULLI I SEKSIONIT..."
                                            className="w-full bg-blue-50 border border-blue-100 rounded-xl py-3 px-4 text-sm font-bold text-blue-700"
                                        />
                                    ) : (
                                        <textarea
                                            value={row.description}
                                            onChange={(e) => updateRow(row.id, { description: e.target.value })}
                                            placeholder={row.row_type === 'text' ? 'Tekst informativ...' : 'Përshkrimi...'}
                                            rows={row.row_type === 'text' ? 2 : 1}
                                            className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-4 text-sm font-medium"
                                        />
                                    )}

                                    {row.row_type === 'item' && (
                                        <div className="flex flex-wrap items-center gap-3">
                                            {row.modules.map((mod) => (
                                                <div key={mod.id} className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
                                                    <input
                                                        type="text"
                                                        value={mod.value}
                                                        onChange={(e) => updateModule(row.id, mod.id, { value: e.target.value })}
                                                        className="w-16 bg-transparent text-sm font-bold outline-none"
                                                        placeholder="0"
                                                    />
                                                    <input
                                                        type="text"
                                                        value={mod.unit}
                                                        onChange={(e) => updateModule(row.id, mod.id, { unit: e.target.value })}
                                                        className="w-12 bg-transparent text-sm font-bold text-blue-600 outline-none"
                                                        placeholder="m²"
                                                    />
                                                    <button onClick={() => removeModule(row.id, mod.id)} className="text-slate-400 hover:text-red-500">
                                                        <X size={14} />
                                                    </button>
                                                </div>
                                            ))}
                                            <button onClick={() => addModule(row.id)} className="px-3 py-2 text-xs font-bold bg-slate-100 rounded-xl hover:bg-slate-200">+</button>
                                            <div className="ml-auto text-sm font-bold text-slate-700">
                                                {calculateRowSubtotal(row).toLocaleString('sq-AL', { minimumFractionDigits: 2 })} €
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="flex flex-col items-end gap-2">
                                    <label className="text-xs text-slate-500 flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={row.has_border}
                                            onChange={(e) => updateRow(row.id, { has_border: e.target.checked })}
                                        />
                                        Kornizë
                                    </label>
                                    <button onClick={() => removeRow(row.id)} className="p-2 text-slate-400 hover:text-red-500">
                                        <X size={16} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch gap-3 bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/60 shadow-sm mt-8">
                <button
                    onClick={handlePreview}
                    disabled={saving}
                    className="w-full sm:flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-slate-100 text-slate-700 rounded-2xl text-sm font-black hover:bg-slate-200 transition-all shadow-sm disabled:opacity-50"
                >
                    <Eye size={20} />
                    <span>SHIKO</span>
                </button>
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
            </div>
        </div>
    )
}

export default OfferForm
