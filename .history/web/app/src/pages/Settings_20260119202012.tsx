import React, { useState, useEffect } from 'react'
import { Save, Building2, Mail, Phone, MapPin, Hash, CreditCard, Server, Shield } from 'lucide-react'
import { motion } from 'framer-motion'
import { CompanyService } from '../services/api'

const SettingsPage = () => {
    const [company, setCompany] = useState<any>({
        name: '',
        address: '',
        phone: '',
        email: '',
        unique_number: '',
        fiscal_number: '',
        account_nib: '',
        smtp_server: 'smtp.gmail.com',
        smtp_port: 587,
        smtp_user: '',
        smtp_password: ''
    })
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })

    useEffect(() => {
        CompanyService.get()
            .then(data => setCompany(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }, [])

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault()
        setSaving(true)
        setMessage({ type: '', text: '' })
        try {
            await CompanyService.update(company)
            setMessage({ type: 'success', text: 'Të dhënat u ruajtën me sukses!' })
        } catch (error) {
            console.error(error)
            setMessage({ type: 'error', text: 'Gabim gjatë ruajtjes!' })
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <div className="p-8 text-center text-gray-500">Duke u ngarkuar...</div>

    return (
        <div className="p-6 md:p-10 max-w-5xl mx-auto w-full pb-20">
            <div className="flex items-center justify-between mb-10">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-slate-800">Cilësimet</h1>
                    <p className="text-sm text-slate-400 font-medium whitespace-nowrap">Menaxhoni profilin e kompanisë suaj dhe sistemin</p>
                </div>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 disabled:opacity-50"
                >
                    <Save size={18} />
                    <span>{saving ? 'Duke Ruajtur...' : 'Ruaj Ndryshimet'}</span>
                </button>
            </div>

            {message.text && (
                <div className={`mb-6 p-4 rounded-xl text-sm font-bold ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Profile Section */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-6">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-2">
                        <Building2 size={20} className="text-blue-500" />
                        Profili i Biznesit
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Emri i Kompanisë</label>
                            <div className="relative">
                                <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                <input
                                    type="text"
                                    value={company.name}
                                    onChange={e => setCompany({ ...company, name: e.target.value })}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Telefoni</label>
                                <div className="relative">
                                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                    <input
                                        type="text"
                                        value={company.phone}
                                        onChange={e => setCompany({ ...company, phone: e.target.value })}
                                        className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                    <input
                                        type="email"
                                        value={company.email}
                                        onChange={e => setCompany({ ...company, email: e.target.value })}
                                        className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                    />
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Adresa</label>
                            <div className="relative">
                                <MapPin className="absolute left-4 top-3 text-slate-300" size={18} />
                                <textarea
                                    rows={2}
                                    value={company.address}
                                    onChange={e => setCompany({ ...company, address: e.target.value })}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Fiscal Section */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-6">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-2">
                        <CreditCard size={20} className="text-blue-500" />
                        Të dhënat Fiskale
                    </h3>

                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Numri Unik</label>
                                <div className="relative">
                                    <Hash className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                    <input
                                        type="text"
                                        value={company.unique_number}
                                        onChange={e => setCompany({ ...company, unique_number: e.target.value })}
                                        className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Numri Fiskal</label>
                                <div className="relative">
                                    <Hash className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                    <input
                                        type="text"
                                        value={company.fiscal_number}
                                        onChange={e => setCompany({ ...company, fiscal_number: e.target.value })}
                                        className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                    />
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Xhirollaria (NIB)</label>
                            <div className="relative">
                                <CreditCard className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                <input
                                    type="text"
                                    value={company.account_nib}
                                    onChange={e => setCompany({ ...company, account_nib: e.target.value })}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* SMTP Section */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-6 lg:col-span-2">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-2">
                        <Server size={20} className="text-blue-500" />
                        Konfigurimi i Email-it (SMTP)
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="lg:col-span-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Hosti SMTP</label>
                            <input
                                type="text"
                                value={company.smtp_server}
                                onChange={e => setCompany({ ...company, smtp_server: e.target.value })}
                                className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Porti</label>
                            <input
                                type="number"
                                value={company.smtp_port}
                                onChange={e => setCompany({ ...company, smtp_port: parseInt(e.target.value) || 587 })}
                                className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                        <div className="hidden lg:block"></div>

                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Përdoruesi SMTP</label>
                            <input
                                type="text"
                                value={company.smtp_user}
                                onChange={e => setCompany({ ...company, smtp_user: e.target.value })}
                                className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Fjalëkalimi SMTP</label>
                            <div className="relative">
                                <Shield className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                <input
                                    type="password"
                                    value={company.smtp_password}
                                    onChange={e => setCompany({ ...company, smtp_password: e.target.value })}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 pr-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>
                    </div>
                    <p className="text-[10px] text-slate-400 italic">Këto të dhëna do të përdoren për të dërguar faturat dhe ofertat direkt me email.</p>
                </div>
            </div>
        </div>
    )
}

export default SettingsPage
