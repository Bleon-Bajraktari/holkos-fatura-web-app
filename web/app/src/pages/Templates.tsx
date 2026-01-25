import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, Star, ToggleLeft, ToggleRight, ArrowLeft } from 'lucide-react'
import { TemplateService } from '../services/api'

const TemplatesPage = () => {
    const navigate = useNavigate()
    const [templates, setTemplates] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const loadTemplates = () => {
        setLoading(true)
        TemplateService.getAll()
            .then(data => setTemplates(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        loadTemplates()
    }, [])

    const handleSetDefault = async (id: number) => {
        await TemplateService.setDefault(id)
        loadTemplates()
    }

    const handleToggleActive = async (id: number) => {
        await TemplateService.toggleActive(id)
        loadTemplates()
    }

    return (
        <div className="p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full">
            <div className="mb-8 flex items-center gap-3">
                <button
                    onClick={() => navigate('/')}
                    className="p-2.5 bg-white border border-gray-200 rounded-xl text-gray-500 hover:text-gray-800 hover:border-gray-300 transition-all shadow-sm"
                >
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h1 className="text-2xl font-bold">Menaxhimi i Shabllonave</h1>
                    <p className="text-gray-500 text-sm mt-1">Shablloni default është i integruar në sistem.</p>
                </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="md:hidden divide-y divide-gray-100">
                    {loading ? (
                        <div className="px-6 py-10 text-center text-gray-400">Duke u ngarkuar...</div>
                    ) : templates.length === 0 ? (
                        <div className="px-6 py-10 text-center text-gray-400">Nuk ka shabllona.</div>
                    ) : (
                        templates.map(template => (
                            <div key={template.id} className="p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <div className="font-bold text-gray-900">{template.name}</div>
                                        <div className="text-xs text-gray-500">{template.description || '-'}</div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {!template.is_default && (
                                            <button
                                                onClick={() => handleSetDefault(template.id)}
                                                className="px-3 py-1.5 text-xs font-bold bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition-colors"
                                            >
                                                Default
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleToggleActive(template.id)}
                                            className="px-3 py-1.5 text-xs font-bold bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors inline-flex items-center gap-1"
                                        >
                                            {template.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                                            {template.is_active ? 'Aktiv' : 'Joaktiv'}
                                        </button>
                                    </div>
                                </div>
                                <div className="mt-3 flex items-center gap-4 text-sm">
                                    <span className={`inline-flex items-center gap-1 font-semibold ${template.is_active ? 'text-green-600' : 'text-red-500'}`}>
                                        <Check size={16} /> {template.is_active ? 'Aktiv' : 'Joaktiv'}
                                    </span>
                                    <span className={`inline-flex items-center gap-1 font-semibold ${template.is_default ? 'text-amber-600' : 'text-gray-400'}`}>
                                        <Star size={16} /> {template.is_default ? 'Default' : 'Jo default'}
                                    </span>
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
                                <th className="px-6 py-4">Përshkrimi</th>
                                <th className="px-6 py-4">Aktiv</th>
                                <th className="px-6 py-4">Default</th>
                                <th className="px-6 py-4 text-right">Veprimet</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-400">Duke u ngarkuar...</td>
                                </tr>
                            ) : templates.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-400">Nuk ka shabllona.</td>
                                </tr>
                            ) : (
                                templates.map(template => (
                                    <tr key={template.id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-gray-900">{template.name}</td>
                                        <td className="px-6 py-4 text-gray-600">{template.description || '-'}</td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {template.is_active ? (
                                                <span className="inline-flex items-center gap-1 text-green-600 font-semibold"><Check size={16} /> Po</span>
                                            ) : (
                                                <span className="text-red-500 font-semibold">Jo</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {template.is_default ? (
                                                <span className="inline-flex items-center gap-1 text-amber-600 font-semibold"><Star size={16} /> Po</span>
                                            ) : (
                                                <span className="text-gray-400">Jo</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="inline-flex items-center gap-2">
                                                {!template.is_default && (
                                                    <button
                                                        onClick={() => handleSetDefault(template.id)}
                                                        className="px-3 py-1.5 text-xs font-bold bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition-colors"
                                                    >
                                                        Default
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => handleToggleActive(template.id)}
                                                    className="px-3 py-1.5 text-xs font-bold bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors inline-flex items-center gap-1"
                                                >
                                                    {template.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                                                    {template.is_active ? 'Aktiv' : 'Joaktiv'}
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

export default TemplatesPage
