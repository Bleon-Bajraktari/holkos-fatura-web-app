import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Save, Download, ArrowLeft } from 'lucide-react'
import { ContractService, CompanyService, openPdf } from '../services/api'

const defaultForm = {
    employee_name: '',
    personal_number: '',
    residence: '',
    contract_date: new Date().toISOString().split('T')[0],
    gross_salary: 0,
}

const ContractForm = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const isEdit = !!id
    const [form, setForm] = useState(defaultForm)
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [company, setCompany] = useState<any>(null)
    const [suggestions, setSuggestions] = useState<any[]>([])
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [suggestionField, setSuggestionField] = useState<'name' | 'number' | null>(null)
    const [allContracts, setAllContracts] = useState<any[]>([])
    const suggestionRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        CompanyService.get().then(setCompany).catch(() => {})
    }, [])

    useEffect(() => {
        if (isEdit && id) {
            setLoading(true)
            ContractService.get(Number(id))
                .then(data => {
                    const dateVal = (data.contract_date || data.contract_start_date || '').toString().slice(0, 10)
                    setForm({
                        employee_name: data.employee_name || '',
                        personal_number: data.personal_number || '',
                        residence: data.residence || '',
                        contract_date: dateVal || new Date().toISOString().split('T')[0],
                        gross_salary: Number(data.gross_salary) || 0,
                    })
                })
                .catch(() => {})
                .finally(() => setLoading(false))
        } else {
            setForm({ ...defaultForm })
        }
    }, [isEdit, id])

    useEffect(() => {
        ContractService.getAll().then(data => setAllContracts(Array.isArray(data) ? data : [])).catch(() => {})
    }, [])

    // Një person vetëm një herë (emër + numër personal unik), edhe nëse ka shumë kontrata
    const uniquePersons = (list: any[]) => {
        const seen = new Set<string>()
        return list.filter(c => {
            const key = `${(c.employee_name || '').trim()}|${(c.personal_number || '').trim()}`
            if (seen.has(key)) return false
            seen.add(key)
            return true
        })
    }

    useEffect(() => {
        if (!showSuggestions || !suggestionField) return
        const term = (suggestionField === 'name' ? form.employee_name : form.personal_number || '').trim().toLowerCase()
        if (term.length < 1) {
            setSuggestions(uniquePersons(allContracts).slice(0, 10))
        } else {
            const filtered = allContracts.filter(c => {
                const name = (c.employee_name || '').toLowerCase()
                const num = (c.personal_number || '').toLowerCase()
                return name.includes(term) || num.includes(term)
            })
            setSuggestions(uniquePersons(filtered).slice(0, 8))
        }
    }, [form.employee_name, form.personal_number, showSuggestions, suggestionField, allContracts])

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (suggestionRef.current && !suggestionRef.current.contains(e.target as Node)) {
                setShowSuggestions(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const applySuggestion = (c: any) => {
        setForm(prev => ({
            ...prev,
            employee_name: c.employee_name || prev.employee_name,
            personal_number: c.personal_number || prev.personal_number,
            residence: c.residence || prev.residence,
        }))
        setShowSuggestions(false)
        setSuggestionField(null)
    }

    const formatDate = (s: string) => {
        if (!s) return '–'
        try {
            const [y, m, d] = s.split('-')
            return `${d}.${m}.${y}`
        } catch {
            return s
        }
    }
    const formatDateSpaces = (s: string) => {
        if (!s) return '–'
        try {
            const [y, m, d] = s.split('-')
            return `${d} ${m} ${y}`
        } catch {
            return s
        }
    }

    const handleSave = async () => {
        if (!form.employee_name?.trim()) {
            alert('Ju lutem shkruani emrin dhe mbiemrin e punonjësit.')
            return
        }
        if (!form.contract_date) {
            alert('Ju lutem plotësoni datën.')
            return
        }
        const salary = Number(form.gross_salary)
        if (!Number.isFinite(salary) || salary < 0) {
            alert('Paga bruto duhet të jetë një numër pozitiv.')
            return
        }
        setSaving(true)
        try {
            const payload = {
                employee_name: form.employee_name.trim(),
                personal_number: form.personal_number?.trim() || null,
                residence: form.residence?.trim() || null,
                contract_date: form.contract_date,
                gross_salary: salary,
            }
            if (isEdit && id) {
                await ContractService.update(Number(id), payload)
                alert('Kontrata u përditësua.')
                loadContractForPdf(Number(id))
            } else {
                const created = await ContractService.create(payload)
                alert('Kontrata u ruajt.')
                setForm(prev => ({ ...prev }))
                loadContractForPdf(created.id)
            }
        } catch (e) {
            alert('Gabim: ' + (e as any)?.response?.data?.detail || (e as Error)?.message)
        } finally {
            setSaving(false)
        }
    }

    const [savedId, setSavedId] = useState<number | null>(null)
    const loadContractForPdf = (contractId: number) => {
        setSavedId(contractId)
    }
    useEffect(() => {
        if (isEdit && id) setSavedId(Number(id))
    }, [isEdit, id])
    const handleDownloadPdf = async () => {
        const targetId = savedId || (isEdit && id ? Number(id) : null)
        if (targetId == null) {
            alert('Ruajeni kontratën fillimisht, pastaj shkarkoni PDF.')
            return
        }
        try {
            await openPdf(ContractService.getPdfPath(targetId))
        } catch (e) {
            alert('Gabim gjatë hapjes së PDF: ' + (e as any)?.response?.data?.detail || (e as Error)?.message)
        }
    }

    const compName = company?.name || 'Holkos Metal'
    const emp = form.employee_name || '–'
    const persNum = form.personal_number || '–'
    const res = form.residence || '–'
    const compRepFixed = 'Mustafë Bajraktari'
    const salaryStr = Number.isFinite(Number(form.gross_salary)) ? String(Number(form.gross_salary)) : '–'
    const dtSpaces = formatDateSpaces(form.contract_date)
    const dtDots = formatDate(form.contract_date)
    const canPdf = savedId !== null || (isEdit && !!id)

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center text-gray-500 font-medium">Duke u ngarkuar...</div>
        )
    }

    return (
        <div className="min-h-screen pb-16">
            <div className="bg-white border-b border-gray-100 sticky top-0 z-20">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => navigate('/contracts')}
                                className="p-2.5 bg-gray-50 text-gray-500 hover:text-blue-600 rounded-xl"
                            >
                                <ArrowLeft size={18} />
                            </button>
                            <h1 className="text-xl font-black text-gray-900">
                                {isEdit ? 'Redakto kontratën' : 'Kontratë e re'}
                            </h1>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className="bg-blue-600 text-white px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl font-bold text-xs sm:text-sm flex items-center gap-1.5 disabled:opacity-60"
                            >
                                <Save size={16} />
                                {saving ? 'Duke ruajtur...' : 'Ruaj'}
                            </button>
                            {canPdf && (
                                <button
                                    onClick={handleDownloadPdf}
                                    className="bg-gray-100 text-gray-700 px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl font-bold text-xs sm:text-sm flex items-center gap-1.5"
                                >
                                    <Download size={14} />
                                    <span className="hidden sm:inline">Shkarko </span>PDF
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-4 py-6 space-y-8">
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <h2 className="text-lg font-bold text-gray-800 mb-4">Të dhënat e ndryshueshme</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="sm:col-span-2 relative" ref={suggestionRef}>
                            <label className="block text-xs font-bold text-gray-500 mb-1">Emri dhe mbiemri i punonjësit</label>
                            <input
                                type="text"
                                value={form.employee_name}
                                onChange={e => setForm(f => ({ ...f, employee_name: e.target.value }))}
                                onFocus={() => { setShowSuggestions(true); setSuggestionField('name'); }}
                                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm"
                                placeholder="Emri dhe Mbiemri"
                            />
                            {showSuggestions && suggestionField === 'name' && suggestions.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-10 max-h-48 overflow-auto">
                                    {suggestions.map(c => (
                                        <button
                                            key={c.id}
                                            type="button"
                                            onClick={() => applySuggestion(c)}
                                            className="w-full text-left px-4 py-2 hover:bg-blue-50 text-sm"
                                        >
                                            {c.employee_name} {c.personal_number ? `(${c.personal_number})` : ''}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="relative" ref={suggestionField === 'number' ? suggestionRef : undefined}>
                            <label className="block text-xs font-bold text-gray-500 mb-1">Numri personal</label>
                            <input
                                type="text"
                                inputMode="numeric"
                                pattern="[0-9]*"
                                value={form.personal_number}
                                onChange={e => setForm(f => ({ ...f, personal_number: e.target.value }))}
                                onFocus={() => { setShowSuggestions(true); setSuggestionField('number'); }}
                                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm"
                                placeholder="Nr. Personal"
                            />
                            {showSuggestions && suggestionField === 'number' && suggestions.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-10 max-h-48 overflow-auto">
                                    {suggestions.map(c => (
                                        <button
                                            key={c.id}
                                            type="button"
                                            onClick={() => applySuggestion(c)}
                                            className="w-full text-left px-4 py-2 hover:bg-blue-50 text-sm"
                                        >
                                            {c.personal_number} – {c.employee_name}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 mb-1">Vendbanimi</label>
                            <input
                                type="text"
                                value={form.residence}
                                onChange={e => setForm(f => ({ ...f, residence: e.target.value }))}
                                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm"
                                placeholder="Vendbanimi"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 mb-1">Data e kontratës</label>
                            <input
                                type="date"
                                value={form.contract_date}
                                onChange={e => setForm(f => ({ ...f, contract_date: e.target.value }))}
                                className="w-full min-w-0 max-w-full border border-gray-200 rounded-xl h-10 px-3 text-[13px] font-medium focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all appearance-none"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 mb-1">Paga bruto (euro)</label>
                            <input
                                type="number"
                                inputMode="numeric"
                                min={0}
                                step={1}
                                value={form.gross_salary}
                                onChange={e => setForm(f => ({ ...f, gross_salary: e.target.value === '' ? 0 : Number(e.target.value) }))}
                                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm"
                            />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <h2 className="text-lg font-bold text-gray-800 mb-4">Parashikim i kontratës</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-3 max-h-[60vh] overflow-y-auto pr-2 contract-preview whitespace-pre-line">
                        <p className="font-bold">Kontratë e Re.</p>
                        <p>Në bazë të nenit 10 paragrafi 2, pikat 2.1 dhe 2.2. dhe nenit 11 të Ligjit të Punës Nr. 03/L-212 i shpallur në Gazetën Zyrtare të Republikës së Kosovës me dt.01.12.2010, Punëdhënësi dhe i Punësuari, si subjekte të mardhënies juridike të punës lidhin:</p>
                        <p className="text-center font-bold text-base">KONTRATË PUNE PËR KOHË TË PACAKTUAR</p>
                        <p><strong>Neni 1</strong><br/>Me këtë kontratë: NTP &quot;{compName}&quot; përfaqësuar nga {compRepFixed}, NF … (Emri/emërtimi, NRB, NF dhe adresa e punëdhënësit) Në tekstin e metejmë Punëdhënësi lidhë kontratë pune me<br/><span className="underline">{emp}</span> NP <span className="underline">{persNum}</span> – me banim <span className="underline">{res}</span><br/>(Emri dhe mbiemri, kualifikimi, adresa dhe numri personal)</p>
                        <p><strong>Neni 2</strong><br/>I Punësuari do të kryej këto detyra të punës: Punetor<br/>(Emërtimi, natyra, lloji i punës dhe përshkrimi i detyrave të punës)</p>
                        <p><strong>Neni 3</strong><br/>I Punësuari do të kryej punët në: Terren sipas nevojes se NTP &quot;{compName}&quot;<br/>(vendi i punës ku do të kryhet puna apo në lokacione të ndryshme)</p>
                        <p><strong>Neni 4</strong><br/>I Punësuari themelon mardhënie pune në kohë të pacaktuar që nga data: <span className="underline">{dtSpaces}</span>.</p>
                        <p><strong>Neni 5</strong><br/>I Punësuari është i detyruar të filloj punën me: <span className="underline">{dtDots}</span>. Nëse i punësuari nuk e fillon punën në ditën e caktuar sipas kësaj kontrate, do të konsiderohet se nuk ka themeluar mardhanie pune, përvec nëse është penguar për shkaqe të arsyeshme.</p>
                        <p><strong>Neni 6</strong><br/>Ditë pune janë nga e hëna në të premte me nga 8 orë pune, gjithsej 40 orë në javë.</p>
                        <p><strong>Neni 7</strong><br/>Të punësuarit i caktohet paga bazë për punën të cilën e kryen për punëdhënësin, në lartësi prej Bruto <span className="underline">{salaryStr} euro</span>, së paku një herë në muaj e cila nuk mund të jetë më e vogël se paga minimale.</p>
                        <p><strong>Neni 8</strong> – I punësuari ka të drejtë në pagë shtesë… (20%, 30%, 30%, 50%, 50%).</p>
                        <p><strong>Neni 9</strong> – I punësuari ka të drejtë në kompezim…</p>
                        <p><strong>Neni 10</strong> – I punësuari ka të drejtë në kompensim të pushimit mjekësor…</p>
                        <p><strong>Neni 11</strong> – I punësuari ka të drejtë në pushim…</p>
                        <p><strong>Neni 12</strong> – I punësuari… ka të drejtën e shfrytezimit të pushimit vjetor pas gjashtë (6) muajve…</p>
                        <p><strong>Neni 13</strong> – I punësuari ka të drejtë së paku një ditë e gjysmë (1.5) të pushimit…</p>
                        <p><strong>Neni 14</strong> – I punësuari është përgjegjës për kompenzimin e dëmit…</p>
                        <p><strong>Neni 15</strong> – Të punësuarit i ndërprehet mardhënia e punës…</p>
                        <p><strong>Neni 16</strong> – Punëdhënësi obligohet të siguroj dhe të zbatoj mjetet e mbrojtjes në punë…</p>
                        <p><strong>Neni 17</strong> – Punëdhënësi obligohet t&apos;i paguaj kontributet prej 5%…</p>
                        <p><strong>Neni 18</strong> – Punëdhënësi dhe i punësuari i pranojnë të gjitha të drejtat…</p>
                        <p><strong>Neni 19</strong> – Për kontestet eventuale… Gjykata Komunale në Peje.</p>
                        <p><strong>Neni 20</strong> – Secila palë mund t&apos;a shkëputë këtë Kontratë…</p>
                        <p><strong>Neni 21</strong> – Në asnjë rast, dispozitat e kësaj Kontratë nuk mund të jenë me pak të favorshme…</p>
                        <p><strong>Neni 22</strong><br/>Pas njoftimit me përmbajtjen e Kontratës, kjo Kontratë nga palët kontraktuese u nënshkrua me <span className="underline">{dtSpaces}</span>.<br/>Në Peje dhe atë në 5 kopje autentike, nga të cilat secilës palë i mbeten nga dy (2) kopje.</p>
                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 mt-4">
                            <div>
                                <p className="font-bold text-gray-800">Punëdhenesi:</p>
                                <p>{compName}</p>
                                <p>{compRepFixed}</p>
                            </div>
                            <div>
                                <p className="font-bold text-gray-800">I Punësuari:</p>
                                <p className="underline">{emp}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ContractForm
