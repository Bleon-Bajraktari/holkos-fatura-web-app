import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Save, Building2, Mail, Phone, MapPin, Hash, CreditCard, Server, Shield, ArrowLeft, Trash2, Lock, User } from 'lucide-react'
import PasswordInput from '../components/PasswordInput'
import { CompanyService, SettingsService, AuthService, API_BASE } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { db } from '../services/db'

const SettingsPage = () => {
    const navigate = useNavigate()
    const { user, updateSession } = useAuth()
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
    const [loadError, setLoadError] = useState<string | null>(null)
    const [paymentStatusEnabled, setPaymentStatusEnabled] = useState(true)
    const [navbarCombined, setNavbarCombined] = useState(true)
    const [logoUploading, setLogoUploading] = useState(false)
    const [resettingCache, setResettingCache] = useState(false)
    const [resettingAll, setResettingAll] = useState(false)
    const [currentPassword, setCurrentPassword] = useState('')
    const [newPassword, setNewPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [changingPassword, setChangingPassword] = useState(false)
    const [passwordChangeMsg, setPasswordChangeMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
    const [newUsername, setNewUsername] = useState('')
    const [usernamePassword, setUsernamePassword] = useState('')
    const [changingUsername, setChangingUsername] = useState(false)
    const [usernameChangeMsg, setUsernameChangeMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

    const defaults = {
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
    }

    const mergeCompany = (data: any) => {
        if (!data || typeof data !== 'object') return defaults
        return { ...defaults, ...data }
    }

    useEffect(() => {
        const load = async () => {
            setLoadError(null)
            const fetchCompany = async (retries = 1): Promise<any> => {
                try {
                    return await CompanyService.get()
                } catch (e) {
                    if (retries > 0) {
                        await new Promise(r => setTimeout(r, 2500))
                        return fetchCompany(retries - 1)
                    }
                    throw e
                }
            }
            try {
                const [companyData, paymentData, navbarData] = await Promise.allSettled([
                    fetchCompany(),
                    SettingsService.getPaymentStatus(),
                    SettingsService.getNavbarCombined()
                ])
                if (companyData.status === 'fulfilled' && companyData.value) {
                    setCompany(mergeCompany(companyData.value))
                    localStorage.setItem('company_cache', JSON.stringify(companyData.value))
                } else if (companyData.status === 'fulfilled' && !companyData.value) {
                    setCompany(mergeCompany({}))
                } else if (companyData.status === 'rejected') {
                    try {
                        const cached = localStorage.getItem('company_cache')
                        if (cached) {
                            setCompany(mergeCompany(JSON.parse(cached)))
                            setLoadError('Të dhënat e shfaqura janë nga cache. Rifreskoni për të marrë nga serveri.')
                        } else {
                            const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                            setLoadError(isLocalhost
                                ? 'Backend nuk është i lidhur. Nisni serverin: cd web/backend && uvicorn main:app --reload --port 8000. Mund të plotësoni fushat dhe të ruani kur backend-i të jetë gati.'
                                : 'Lidhja me backend dështoi (serveri mund të jetë duke u ngrohur). Mund të plotësoni fushat dhe të ruani, ose rifreskoni pas disa sekondash.')
                        }
                    } catch (_) {
                        setLoadError('Backend nuk është i lidhur. Filloni serverin nga web/backend dhe rifreskoni faqen.')
                    }
                }
                if (paymentData.status === 'fulfilled' && paymentData.value?.enabled !== undefined) {
                    setPaymentStatusEnabled(paymentData.value.enabled)
                }
                if (navbarData.status === 'fulfilled' && navbarData.value?.combined !== undefined) {
                    setNavbarCombined(navbarData.value.combined)
                }
            } catch (err) {
                console.error('Settings load error:', err)
                setLoadError('Gabim gjatë ngarkimit. Provoni të rifreskoni faqen.')
                try {
                    const cached = localStorage.getItem('company_cache')
                    if (cached) setCompany(mergeCompany(JSON.parse(cached)))
                } catch (_) {}
            } finally {
                setLoading(false)
            }
        }
        load()
    }, [])

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault()
        setSaving(true)
        setMessage({ type: '', text: '' })
        try {
            await CompanyService.update(company)
            await SettingsService.updatePaymentStatus(paymentStatusEnabled)
            await SettingsService.updateNavbarCombined(navbarCombined)
            localStorage.setItem('company_cache', JSON.stringify(company))
            setMessage({ type: 'success', text: 'Të dhënat u ruajtën me sukses!' })
        } catch (error) {
            console.error(error)
            setMessage({ type: 'error', text: 'Gabim gjatë ruajtjes!' })
        } finally {
            setSaving(false)
        }
    }

    const handleLogoUpload = async (file: File) => {
        if (!file) return
        setLogoUploading(true)
        setMessage({ type: '', text: '' })
        try {
            const updated = await CompanyService.uploadLogo(file)
            setCompany(updated)
            localStorage.setItem('company_cache', JSON.stringify(updated));
            setMessage({ type: 'success', text: 'Logo u ngarkua me sukses!' })
        } catch (error) {
            console.error(error)
            setMessage({ type: 'error', text: 'Gabim gjatë ngarkimit të logos!' })
        } finally {
            setLogoUploading(false)
        }
    }

    const clearCacheStorage = async () => {
        if ('caches' in window) {
            const cacheNames = await caches.keys()
            await Promise.all(cacheNames.map(name => caches.delete(name)))
        }
    }

    const unregisterServiceWorkers = async () => {
        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations()
            await Promise.all(registrations.map(reg => reg.unregister()))
        }
    }

    if (loading) return <div className="p-8 text-center text-gray-500">Duke u ngarkuar...</div>

    return (
        <div className="p-4 sm:p-6 md:p-10 max-w-5xl mx-auto w-full pb-20">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2.5 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-800 hover:border-slate-300 transition-all shadow-sm"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Cilësimet</h1>
                        <p className="text-sm text-slate-400 font-medium">Menaxhoni profilin e kompanisë suaj dhe sistemin</p>
                    </div>
                </div>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 disabled:opacity-50"
                >
                    <Save size={18} />
                    <span>{saving ? 'Duke Ruajtur...' : 'Ruaj Ndryshimet'}</span>
                </button>
            </div>

            {loadError && (
                <div className="mb-6 p-4 rounded-xl text-sm font-bold bg-amber-50 text-amber-800 border border-amber-200">
                    {loadError}
                </div>
            )}
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
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Logo e Kompanisë</label>
                            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0]
                                        if (file) handleLogoUpload(file)
                                    }}
                                    className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-2.5 px-4 text-sm font-bold text-slate-600 file:mr-3 file:rounded-xl file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-xs file:font-bold file:text-white hover:file:bg-blue-700"
                                />
                                <div className="text-xs text-slate-400 font-medium">
                                    {logoUploading ? 'Duke ngarkuar...' : (company.logo_path ? `Logo: ${company.logo_path}` : 'Nuk ka logo')}
                                </div>
                            </div>
                            {company.logo_path && (
                                <div className="mt-3">
                                    <img
                                        src={API_BASE && API_BASE.startsWith('http')
                                            ? `${API_BASE.replace(/\/$/, '')}/${company.logo_path.replace(/^\/+/, '')}`
                                            : `/${company.logo_path.replace(/^\/+/, '')}`}
                                        alt="Logo"
                                        className="h-14 w-auto rounded-lg border border-slate-200 bg-white p-1"
                                    />
                                </div>
                            )}
                        </div>
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
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Xhirollaria (NLB)</label>
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
                                <Shield className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 z-10" size={18} />
                                <PasswordInput
                                    value={company.smtp_password}
                                    onChange={e => setCompany({ ...company, smtp_password: e.target.value })}
                                    inputClassName="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 pl-12 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                                />
                            </div>
                        </div>
                    </div>
                    <p className="text-[10px] text-slate-400 italic">Këto të dhëna do të përdoren për të dërguar faturat dhe ofertat direkt me email.</p>
                </div>

                {/* App Settings */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-4 lg:col-span-2">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-2">
                        <Shield size={20} className="text-blue-500" />
                        Cilësimet e Aplikacionit
                    </h3>
                    <label className="flex items-center gap-3 text-sm font-semibold text-slate-700">
                        <input
                            type="checkbox"
                            checked={paymentStatusEnabled}
                            onChange={(e) => setPaymentStatusEnabled(e.target.checked)}
                            className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/30"
                        />
                        Aktivizo Menaxhimin e Statusit (Paguar/Pa Paguar)
                    </label>
                    <label className="flex items-center gap-3 text-sm font-semibold text-slate-700 mt-4 pt-4 border-t border-slate-100">
                        <input
                            type="checkbox"
                            checked={navbarCombined}
                            onChange={(e) => setNavbarCombined(e.target.checked)}
                            className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/30"
                        />
                        Menyja e bashkuar (një link për Faturat, Ofertat, Kontratat). Çaktivizo për të ndarë: Faturë e re, Lista e faturave, Ofertë e re, Lista e ofertave, Kontratë e re, Lista e kontratave.
                    </label>
                </div>

                {/* Change Username */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-4 lg:col-span-2">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-2">
                        <User size={20} className="text-blue-500" />
                        Ndrysho Emrin e Përdoruesit
                    </h3>
                    {user && (
                        <p className="text-sm text-slate-500">Përdoruesi aktual: <span className="font-bold text-slate-700">{user.username}</span></p>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Emri i ri i përdoruesit</label>
                            <input
                                type="text"
                                value={newUsername}
                                onChange={(e) => setNewUsername(e.target.value)}
                                placeholder="p.sh. admin"
                                className="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Fjalëkalimi aktual (konfirmim)</label>
                            <PasswordInput
                                value={usernamePassword}
                                onChange={(e) => setUsernamePassword(e.target.value)}
                                placeholder="••••••••"
                                inputClassName="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                    </div>
                    {usernameChangeMsg && (
                        <div className={`p-4 rounded-xl text-sm font-bold ${usernameChangeMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                            {usernameChangeMsg.text}
                        </div>
                    )}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <button
                            type="button"
                            disabled={changingUsername || !newUsername.trim() || !usernamePassword || newUsername.trim().length < 2}
                            onClick={async () => {
                                setUsernameChangeMsg(null)
                                const un = newUsername.trim()
                                if (un.length < 2) {
                                    setUsernameChangeMsg({ type: 'error', text: 'Emri duhet të ketë të paktën 2 karaktere.' })
                                    return
                                }
                                setChangingUsername(true)
                                try {
                                    const res = await AuthService.changeUsername(usernamePassword, un)
                                    if (res?.access_token) {
                                        updateSession(res.access_token, un)
                                    }
                                    setUsernameChangeMsg({ type: 'success', text: 'Emri i përdoruesit u ndryshua me sukses! Më pas hyni me emrin e ri.' })
                                    setNewUsername('')
                                    setUsernamePassword('')
                                } catch (err: any) {
                                    const detail = err?.response?.data?.detail
                                    const text = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail[0] : 'Fjalëkalimi është i gabuar.')
                                    setUsernameChangeMsg({ type: 'error', text })
                                } finally {
                                    setChangingUsername(false)
                                }
                            }}
                            className="flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {changingUsername ? 'Duke ndryshuar...' : 'Ndrysho Emrin'}
                        </button>
                        <p className="text-xs text-slate-500">
                            Emri duhet të ketë të paktën 2 karaktere. Për ndryshim kërkohet fjalëkalimi aktual.
                        </p>
                    </div>
                </div>

                {/* Change Password */}
                <div className="bg-white p-8 rounded-3xl border border-slate-200/60 shadow-sm space-y-4 lg:col-span-2">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-2">
                        <Lock size={20} className="text-blue-500" />
                        Ndrysho Fjalëkalimin
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Fjalëkalimi aktual</label>
                            <PasswordInput
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                                placeholder="••••••••"
                                inputClassName="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Fjalëkalimi i ri</label>
                            <PasswordInput
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="••••••••"
                                inputClassName="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 block">Konfirmo fjalëkalimin e ri</label>
                            <PasswordInput
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                inputClassName="w-full bg-slate-50 border border-slate-100 rounded-2xl py-3 px-4 text-sm font-bold focus:ring-2 focus:ring-blue-600/10 focus:bg-white transition-all"
                            />
                        </div>
                    </div>
                    {passwordChangeMsg && (
                        <div className={`p-4 rounded-xl text-sm font-bold ${passwordChangeMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                            {passwordChangeMsg.text}
                        </div>
                    )}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <button
                            type="button"
                            disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword || newPassword !== confirmPassword || newPassword.length < 4}
                            onClick={async () => {
                                setPasswordChangeMsg(null)
                                if (newPassword !== confirmPassword) {
                                    setPasswordChangeMsg({ type: 'error', text: 'Fjalëkalimet e reja nuk përputhen.' })
                                    return
                                }
                                if (newPassword.length < 4) {
                                    setPasswordChangeMsg({ type: 'error', text: 'Fjalëkalimi i ri duhet të ketë të paktën 4 karaktere.' })
                                    return
                                }
                                setChangingPassword(true)
                                try {
                                    await AuthService.changePassword(currentPassword, newPassword)
                                    setPasswordChangeMsg({ type: 'success', text: 'Fjalëkalimi u ndryshua me sukses! Mund të hyni me fjalëkalimin e ri.' })
                                    setCurrentPassword('')
                                    setNewPassword('')
                                    setConfirmPassword('')
                                } catch (err: any) {
                                    const detail = err?.response?.data?.detail
                                    const text = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail[0] : 'Fjalëkalimi aktual është i gabuar.')
                                    setPasswordChangeMsg({ type: 'error', text })
                                } finally {
                                    setChangingPassword(false)
                                }
                            }}
                            className="flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {changingPassword ? 'Duke ndryshuar...' : 'Ndrysho Fjalëkalimin'}
                        </button>
                        <p className="text-xs text-slate-500">
                            Fjalëkalimi duhet të ketë të paktën 4 karaktere.
                        </p>
                    </div>
                </div>

                {/* Advanced & Troubleshooting Section */}
                <div className="bg-white p-8 rounded-3xl border border-rose-200 shadow-sm space-y-4 lg:col-span-2 border-dashed bg-rose-50/10">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div>
                            <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-1">
                                <Server size={20} className="text-rose-600" />
                                Zgjidhja e Problemeve (PWA & Cache)
                            </h3>
                            <p className="text-xs text-slate-500 max-w-xl">
                                Përdoreni këtë buton nëse keni probleme me: <span className="font-bold">të dhëna të vjetra në listat e faturave/ofertave, logon, ose hapjen offline.</span> Pastron cache-in, IndexedDB (fatura, oferta, klientë) dhe Service Worker. Cilësimet mbeten. Për fshirje totale përdorni Reset Total.
                            </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2">
                            <button
                                type="button"
                                disabled={resettingCache || resettingAll}
                                onClick={async () => {
                                    if (confirm('Kjo do të pastrojë cache-in, të dhënat e listave (fatura, oferta, klientë) dhe Service Worker. Të dhënat e Cilësimeve mbeten. Vazhdoni?')) {
                                        setResettingCache(true)
                                        try {
                                            await db.invoices.clear()
                                            await db.offers.clear()
                                            await db.clients.clear()
                                            localStorage.removeItem('dashboard_cache')
                                            Object.keys(localStorage).filter(k => k.startsWith('years_cache_')).forEach(k => { try { localStorage.removeItem(k) } catch (_) {} })
                                            await clearCacheStorage()
                                            await unregisterServiceWorkers()
                                            alert('Cache u pastrua! Aplikacioni do të rifreskohet dhe do të ngarkojë të dhënat e reja.')
                                            window.location.reload()
                                        } catch (err) {
                                            console.error('Cache reset failed:', err)
                                            alert('Pati një gabim gjatë pastrimit të cache. Provoni manualisht.')
                                        } finally {
                                            setResettingCache(false)
                                        }
                                    }
                                }}
                                className="flex items-center justify-center gap-2 px-5 py-3 bg-slate-900 text-white rounded-xl text-xs font-black hover:bg-slate-950 transition-all shadow-lg shadow-slate-200 disabled:opacity-60"
                            >
                                <Trash2 size={16} />
                                {resettingCache ? 'Duke pastruar...' : 'PASTRO CACHE (REKOMANDUAR)'}
                            </button>
                            <button
                                type="button"
                                disabled={resettingCache || resettingAll}
                                onClick={async () => {
                                    if (confirm('KUJDES: Kjo do të fshijë të gjitha të dhënat lokale (IndexedDB + LocalStorage), do të çregjistrojë Service Worker dhe do të rifreskojë aplikacionin. Vazhdoni?')) {
                                        setResettingAll(true)
                                        try {
                                            await db.invoices.clear()
                                            await db.offers.clear()
                                            await db.clients.clear()
                                            localStorage.clear()
                                            await clearCacheStorage()
                                            await unregisterServiceWorkers()
                                            alert('Reset total u krye! Aplikacioni do të rifreskohet.')
                                            window.location.reload()
                                        } catch (err) {
                                            console.error('Reset failed:', err)
                                            alert('Pati një gabim gjatë reset-it total. Provoni manualisht.')
                                        } finally {
                                            setResettingAll(false)
                                        }
                                    }
                                }}
                                className="flex items-center justify-center gap-2 px-5 py-3 bg-rose-600 text-white rounded-xl text-xs font-black hover:bg-rose-700 transition-all shadow-lg shadow-rose-200 disabled:opacity-60"
                            >
                                <Trash2 size={16} />
                                {resettingAll ? 'Duke resetuar...' : 'RESET TOTAL'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default SettingsPage
