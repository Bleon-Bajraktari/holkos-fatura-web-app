import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
});

export const InvoiceService = {
    getAll: (params?: any) => api.get('/invoices', { params }).then(res => res.data),
    getOne: (id: number) => api.get(`/invoices/${id}`).then(res => res.data),
    create: (data: any) => api.post('/invoices', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/invoices/${id}`, data).then(res => res.data),
    getNextNumber: () => api.get('/invoices/next-number').then(res => res.data),
    getYears: () => api.get('/invoices/years').then(res => res.data),
    delete: (id: number) => api.delete(`/invoices/${id}`).then(res => res.data),
    updateStatus: (id: number, status: string) => api.put(`/invoices/${id}/status`, { status }).then(res => res.data),
    bulkEmail: (invoice_ids: number[], override_email?: string) => api.post('/invoices/bulk-email', { invoice_ids, override_email }).then(res => res.data),
    bulkDelete: (invoice_ids: number[]) => api.post('/invoices/bulk-delete', { invoice_ids }).then(res => res.data),
    email: (id: number, dest_email?: string) => api.post(`/invoices/${id}/email`, dest_email ? { dest_email } : {}).then(res => res.data),
};

export const OfferService = {
    getAll: (params?: any) => api.get('/offers', { params }).then(res => res.data),
    getOne: (id: number) => api.get(`/offers/${id}`).then(res => res.data),
    create: (data: any) => api.post('/offers', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/offers/${id}`, data).then(res => res.data),
    getNextNumber: () => api.get('/offers/next-number').then(res => res.data),
    getYears: () => api.get('/offers/years').then(res => res.data),
    delete: (id: number) => api.delete(`/offers/${id}`).then(res => res.data),
    bulkEmail: (offer_ids: number[], override_email?: string) => api.post('/offers/bulk-email', { offer_ids, override_email }).then(res => res.data),
    bulkDelete: (offer_ids: number[]) => api.post('/offers/bulk-delete', { offer_ids }).then(res => res.data),
    email: (id: number, dest_email?: string) => api.post(`/offers/${id}/email`, dest_email ? { dest_email } : {}).then(res => res.data),
};

export const ClientService = {
    getAll: () => api.get('/clients').then(res => res.data),
    create: (data: any) => api.post('/clients', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/clients/${id}`, data).then(res => res.data),
    delete: (id: number) => api.delete(`/clients/${id}`).then(res => res.data),
};

export const CompanyService = {
    get: () => api.get('/company').then(res => res.data),
    update: (data: any) => api.put('/company', data).then(res => res.data),
    uploadLogo: (file: File) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/company/logo', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }).then(res => res.data)
    },
};

export const DashboardService = {
    getStats: () => api.get('/dashboard/stats').then(res => res.data),
};

export const SettingsService = {
    getPaymentStatus: () => api.get('/settings/feature-payment-status').then(res => res.data),
    updatePaymentStatus: (enabled: boolean) => api.put('/settings/feature-payment-status', { enabled }).then(res => res.data),
};

export const TemplateService = {
    getAll: () => api.get('/templates').then(res => res.data),
    setDefault: (id: number) => api.put(`/templates/${id}/default`).then(res => res.data),
    toggleActive: (id: number) => api.put(`/templates/${id}/toggle-active`).then(res => res.data),
};

export default api;
