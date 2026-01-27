import axios from 'axios';
import { OfflineService } from './offline';
import { db } from './db';

const api = axios.create({
    baseURL: '/api',
});

// Helper for offline filtering
const filterLocalData = (data: any[], params: any) => {
    let filtered = [...data];
    if (params.search) {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(f =>
            f.invoice_number?.toLowerCase().includes(s) ||
            f.offer_number?.toLowerCase().includes(s) ||
            f.client?.name?.toLowerCase().includes(s)
        );
    }
    if (params.date_from) {
        filtered = filtered.filter(f => f.date >= params.date_from);
    }
    if (params.date_to) {
        filtered = filtered.filter(f => f.date <= params.date_to);
    }
    return filtered;
};

// Normalizojmë URL-në për kontroll të saktë (Heqim /api nëse ekziston)
const getCleanUrl = (url?: string) => {
    if (!url) return '';
    // Heqim domain-in, parametrat dhe çdo gjë para rrugës relative
    let clean = url.split('?')[0].replace(/^(https?:\/\/[^\/]+)?/, '');
    if (clean.includes(':5173')) clean = clean.split(':5173')[1] || clean; // Heqim portën nëse mbetet
    if (clean.startsWith('/api')) clean = clean.substring(4);
    if (!clean.startsWith('/')) clean = '/' + clean;
    return clean;
};

// Sync data to Local IndexedDB (PWA Backup)
api.interceptors.response.use(
    async (response) => {
        const config = response.config;
        const data = response.data;
        const url = getCleanUrl(config.url);

        if (config.method === 'get' && data) {
            try {
                if (url === '/invoices' && Array.isArray(data)) {
                    const items = data.map(inv => ({
                        id: inv.id, invoice_number: inv.invoice_number, date: inv.date, total: inv.total, data: inv, last_sync: Date.now()
                    }));
                    await db.invoices.bulkPut(items);
                } else if (url === '/offers' && Array.isArray(data)) {
                    const items = data.map(off => ({
                        id: off.id, offer_number: off.offer_number, date: off.date, total: off.total, data: off, last_sync: Date.now()
                    }));
                    await db.offers.bulkPut(items);
                } else if (url === '/clients' && Array.isArray(data)) {
                    const items = data.map(c => ({
                        id: c.id, name: c.name, data: c, last_sync: Date.now()
                    }));
                    await db.clients.bulkPut(items);
                } else if (url === '/company') {
                    localStorage.setItem('company_cache', JSON.stringify(data));
                } else if (url === '/dashboard/stats') {
                    localStorage.setItem('dashboard_cache', JSON.stringify(data));
                } else if (url.includes('/years')) {
                    localStorage.setItem(`years_cache_${url}`, JSON.stringify(data));
                }
            } catch (e) {
                console.warn('Backup error (Non-blocking):', e);
            }
        }
        return response;
    },
    async (error) => {
        const config = error.config;
        if (!config) return Promise.reject(error);
        const url = getCleanUrl(config.url);

        // Network error (Offline)
        if (!error.response) {
            console.log(`[Offline Mode] Intercepting GET ${url}`);
            if (config.method === 'get') {
                try {
                    let recoveredData = null;
                    if (url === '/invoices') {
                        const local = await db.invoices.toArray();
                        recoveredData = filterLocalData(local.map(l => l.data), config.params || {});
                    } else if (url === '/offers') {
                        const local = await db.offers.toArray();
                        recoveredData = filterLocalData(local.map(l => l.data), config.params || {});
                    } else if (url === '/clients') {
                        const local = await db.clients.toArray();
                        recoveredData = local.map(l => l.data);
                    } else if (url === '/company') {
                        const cached = localStorage.getItem('company_cache');
                        recoveredData = cached ? JSON.parse(cached) : null;
                    } else if (url === '/dashboard/stats') {
                        const cached = localStorage.getItem('dashboard_cache');
                        recoveredData = cached ? JSON.parse(cached) : null;
                    } else if (url.includes('/years')) {
                        const cached = localStorage.getItem(`years_cache_${url}`);
                        recoveredData = cached ? JSON.parse(cached) : null;
                    }

                    if (recoveredData !== null) {
                        console.log(`[Offline Mode] Success recovered ${url} from cache`);
                        return Promise.resolve({
                            data: recoveredData,
                            status: 200,
                            statusText: 'OK (Offline Cache)',
                            headers: {},
                            config: config
                        });
                    }
                } catch (e) {
                    console.error('Offline recovery fatal error:', e);
                }
            }

            // Mutations (POST/PUT/DELETE)
            if (['post', 'put', 'delete'].includes(config.method || '') && !config.headers?.['X-Sync-Action']) {
                let title = 'Veprim i ri';
                if (url.includes('invoices')) title = 'Ruajtje fature';
                if (url.includes('offers')) title = 'Ruajtje oferte';

                OfflineService.addToQueue(config.method!, config.url!, config.data, title);
                return Promise.resolve({
                    data: { message: 'Ruajtur lokalisht.', _isOffline: true },
                    status: 202,
                    statusText: 'Accepted (Queued)',
                    headers: {},
                    config: config
                });
            }
        }
        return Promise.reject(error);
    }
);

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
