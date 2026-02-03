import axios from 'axios';
import { OfflineService } from './offline';
import { db } from './db';

export const API_BASE = import.meta.env.VITE_API_BASE || '/api';

/** Hap PDF me auth – fetch me token, pastaj blob URL (shmang "Not authenticated" kur hapet në tab të ri) */
export async function openPdf(path: string) {
    const res = await api.get(path, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    window.open(url, '_blank', 'noopener,noreferrer');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

/** Hap PDF nga POST (p.sh. preview i ofertës) */
export async function openPdfPost(path: string, body: object) {
    const res = await api.post(path, body, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    window.open(url, '_blank', 'noopener,noreferrer');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
});

const TOKEN_KEY = 'holkos_token';

// --- REQUEST INTERCEPTOR: add Authorization header ---
api.interceptors.request.use((config) => {
    const url = (config.url || '').split('?')[0];
    if (url === '/auth/login') return config;
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

/** Për SMTP përdorim gjithmonë /api (Vercel function) – mos drejto te Render */
const smtpApi = axios.create({ baseURL: '/api' });

/**
 * Filter Helper for Offline Data
 */
const filterLocalData = (data: any[], params: any) => {
    let filtered = [...data];

    // Sort logic (Newest First)
    // Handle 'temp-' IDs (offline pending) to appear first
    filtered.sort((a, b) => {
        const idA = a.id;
        const idB = b.id;
        const isTempA = typeof idA === 'string' && idA.startsWith('temp-');
        const isTempB = typeof idB === 'string' && idB.startsWith('temp-');

        if (isTempA && !isTempB) return -1; // A (Pending) comes first
        if (!isTempA && isTempB) return 1;  // B (Pending) comes first
        if (isTempA && isTempB) return 0;   // Both pending, keep order

        // Both are numbers (confirmed synced)
        return (Number(idB) || 0) - (Number(idA) || 0);
    });

    if (params?.search && typeof params.search === 'string') {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(f =>
            (String(f?.invoice_number ?? '')).toLowerCase().includes(s) ||
            (String(f?.offer_number ?? '')).toLowerCase().includes(s) ||
            (String(f?.client?.name ?? '')).toLowerCase().includes(s)
        );
    }
    if (params.date_from) {
        filtered = filtered.filter(f => new Date(f.date) >= new Date(params.date_from));
    }
    if (params.date_to) {
        filtered = filtered.filter(f => new Date(f.date) <= new Date(params.date_to));
    }
    return filtered;
};

const buildTempId = (actionId: string) => `temp-${actionId}`;

const isRootCollectionUrl = (url: string, entity: 'invoices' | 'offers' | 'clients') =>
    url === `/${entity}` || url.endsWith(`/${entity}`);

const getEntityFromUrl = (url: string) => {
    const match = url.match(/\/(invoices|offers|clients)(?:\/([^/?]+))?/i);
    if (!match) return null;
    return {
        entity: match[1].toLowerCase() as 'invoices' | 'offers' | 'clients',
        id: match[2]
    };
};

const persistOfflineMutation = async (method: string, url: string, payload: any, actionId: string) => {
    const info = getEntityFromUrl(url);
    if (!info) return;

    const { entity, id } = info;
    const tempId = buildTempId(actionId);

    if (method === 'post') {
        if (!isRootCollectionUrl(url, entity)) return;

        const data = {
            ...payload,
            id: tempId,
            status: payload?.status ?? 'pending-sync',
            _isOfflinePending: true
        };

        if (entity === 'invoices') {
            await db.invoices.put({
                id: tempId as any,
                invoice_number: data.invoice_number,
                date: data.date,
                data
            });
        } else if (entity === 'offers') {
            await db.offers.put({
                id: tempId as any,
                offer_number: data.offer_number,
                date: data.date,
                data
            });
        } else if (entity === 'clients') {
            await db.clients.put({
                id: tempId as any,
                name: data.name,
                data
            });
        }
        return;
    }

    if (!id) return;

    if (method === 'put') {
        if (entity === 'invoices') {
            const existing = await db.invoices.get(id as any);
            const data = {
                ...(existing?.data || {}),
                ...payload,
                id: existing?.data?.id ?? id,
                _isOfflinePending: true
            };
            await db.invoices.put({
                id: id as any,
                invoice_number: data.invoice_number || existing?.invoice_number || '',
                date: data.date || existing?.date || new Date().toISOString(),
                data
            });
        } else if (entity === 'offers') {
            const existing = await db.offers.get(id as any);
            const data = {
                ...(existing?.data || {}),
                ...payload,
                id: existing?.data?.id ?? id,
                _isOfflinePending: true
            };
            await db.offers.put({
                id: id as any,
                offer_number: data.offer_number || existing?.offer_number || '',
                date: data.date || existing?.date || new Date().toISOString(),
                data
            });
        } else if (entity === 'clients') {
            const existing = await db.clients.get(id as any);
            const data = {
                ...(existing?.data || {}),
                ...payload,
                id: existing?.data?.id ?? id,
                _isOfflinePending: true
            };
            await db.clients.put({
                id: id as any,
                name: data.name || existing?.name || '',
                data
            });
        }
        return;
    }

    if (method === 'delete') {
        if (entity === 'invoices') await db.invoices.delete(id as any);
        if (entity === 'offers') await db.offers.delete(id as any);
        if (entity === 'clients') await db.clients.delete(id as any);
    }
};

const getOfflineCollectionData = async (url: string, params: any) => {
    if (url === '/invoices') {
        const local = await db.invoices.toArray();
        const localIds = new Set(local.map(l => String(l.id)));
        let allInvoices = local.map(l => l.data);

        const pendingInvoices = (await getPendingItemsForUrl(url))
            .filter(p => !localIds.has(String(p.id)));

        allInvoices = [...pendingInvoices, ...allInvoices];
        return filterLocalData(allInvoices, params || {});
    }

    if (url === '/offers') {
        const local = await db.offers.toArray();
        const localIds = new Set(local.map(l => String(l.id)));
        let allOffers = local.map(l => l.data);

        const pendingOffers = (await getPendingItemsForUrl(url))
            .filter(p => !localIds.has(String(p.id)));

        allOffers = [...pendingOffers, ...allOffers];
        return filterLocalData(allOffers, params || {});
    }

    if (url === '/clients') {
        const local = await db.clients.toArray();
        const localIds = new Set(local.map(l => String(l.id)));
        let allClients = local.map(l => l.data);

        const pendingClients = (await getPendingItemsForUrl(url))
            .filter(p => !localIds.has(String(p.id)));

        allClients = [...pendingClients, ...allClients];
        return allClients.sort((a, b) => {
            if (a._isOfflinePending && !b._isOfflinePending) return -1;
            if (!a._isOfflinePending && b._isOfflinePending) return 1;
            return (String(a?.name ?? '')).localeCompare(String(b?.name ?? ''));
        });
    }

    return null;
};

const normalizePendingDate = (data: any) => {
    const dateValue = data?.date;
    const parsed = dateValue ? new Date(dateValue) : null;
    if (!dateValue || !parsed || Number.isNaN(parsed.getTime())) {
        const fallback = data?.save_timestamp || new Date().toISOString();
        return { ...data, date: fallback };
    }
    return data;
};

const normalizePendingTotals = (data: any) => {
    const items = Array.isArray(data?.items) ? data.items : [];
    if (!items.length) {
        const total = Number(data?.total);
        if (!Number.isFinite(total)) return { ...data, total: 0, subtotal: 0, vat_amount: 0 };
        return data;
    }
    const subtotal = items.reduce((sum: number, item: any) => {
        const qtyRaw = Number(item?.quantity);
        const priceRaw = Number(item?.unit_price);
        const qty = Number.isFinite(qtyRaw) ? qtyRaw : 0;
        const price = Number.isFinite(priceRaw) ? priceRaw : 0;
        return sum + qty * price;
    }, 0);
    const vatPercentage = Number(data?.vat_percentage || 0);
    const vatAmountRaw = Number(data?.vat_amount);
    const vatAmount = Number.isFinite(vatAmountRaw)
        ? vatAmountRaw
        : Number((subtotal * (vatPercentage / 100)).toFixed(2));
    const totalRaw = Number(data?.total);
    const total = Number.isFinite(totalRaw)
        ? totalRaw
        : Number.isFinite(subtotal + vatAmount)
            ? Number((subtotal + vatAmount).toFixed(2))
            : 0;
    return {
        ...data,
        subtotal,
        vat_amount: vatAmount,
        total
    };
};

const resolveClientName = async (clientId: any) => {
    if (!clientId) return null;
    const numericId = typeof clientId === 'string' && /^\d+$/.test(clientId)
        ? Number(clientId)
        : null;
    const client = await db.clients.get(clientId as any) || (numericId !== null ? await db.clients.get(numericId as any) : undefined);
    if (client?.data?.name) return client.data.name;
    const pendingClient = OfflineService.getQueue()
        .filter(q => (q.url === '/clients' || q.url.endsWith('/clients')) && q.method === 'post')
        .find(q => buildTempId(q.id) === String(clientId));
    if (pendingClient?.data?.name) return pendingClient.data.name;
    return null;
};

const ensureClientLabel = async (data: any) => {
    if (data?.client?.name) return data;
    if (!data?.client_id) return data;
    const name = await resolveClientName(data.client_id);
    if (name) return { ...data, client: { name } };
    return data;
};

const normalizeDocForList = async (data: any, type: 'invoices' | 'offers') => {
    let next = normalizePendingTotals(normalizePendingDate(data));
    next = await ensureClientLabel(next);
    if (type === 'invoices' && !next.status) {
        next = { ...next, status: 'pending-sync' };
    }
    return next;
};

const buildPendingItem = async (queueItem: any, type: 'invoices' | 'offers' | 'clients') => {
    let data = {
        ...queueItem.data,
        id: buildTempId(queueItem.id),
        _isOfflinePending: true
    };
    if (type === 'invoices') {
        data = await normalizeDocForList({ ...data, status: data.status ?? 'pending-sync' }, 'invoices');
    } else if (type === 'offers') {
        data = await normalizeDocForList(data, 'offers');
    } else if (type === 'clients') {
        data = normalizePendingDate(data);
    }
    return data;
};

const getPendingItemsForUrl = async (url: string) => {
    if (url === '/invoices') {
        const pending = OfflineService.getQueue()
            .filter(q => (q.url === '/invoices' || q.url.endsWith('/invoices')) && q.method === 'post');
        return Promise.all(pending.map(q => buildPendingItem(q, 'invoices')));
    }
    if (url === '/offers') {
        const pending = OfflineService.getQueue()
            .filter(q => (q.url === '/offers' || q.url.endsWith('/offers')) && q.method === 'post');
        return Promise.all(pending.map(q => buildPendingItem(q, 'offers')));
    }
    if (url === '/clients') {
        const pending = OfflineService.getQueue()
            .filter(q => (q.url === '/clients' || q.url.endsWith('/clients')) && q.method === 'post');
        return Promise.all(pending.map(q => buildPendingItem(q, 'clients')));
    }
    return [];
};

const appendPendingItems = async (items: any[], url: string) => {
    const existingIds = new Set(items.map(item => String(item?.id)));
    const pendingItems = await getPendingItemsForUrl(url);
    const filteredPending = pendingItems.filter(p => !existingIds.has(String(p.id)));
    return [...filteredPending, ...items];
};

// --- RESPONSE INTERCEPTOR ---
api.interceptors.response.use(
    async (response) => {
        const { config, data } = response;
        const url = config.url || '';
        const method = config.method || 'get';

        // 1. CACHE SUCCESSFUL GET REQUESTS (Background Update)
        if (method === 'get') {
            try {
                if (url === '/invoices' && Array.isArray(data)) {
                    await db.invoices.clear(); // Simple strategy: Clear and Replace to avoid stale deletes
                    await db.invoices.bulkPut(data.map((item: any) => ({
                        id: item.id,
                        invoice_number: item.invoice_number,
                        date: item.date,
                        data: item
                    })));
                } else if (url === '/offers' && Array.isArray(data)) {
                    await db.offers.clear();
                    await db.offers.bulkPut(data.map((item: any) => ({
                        id: item.id,
                        offer_number: item.offer_number,
                        date: item.date,
                        data: item
                    })));
                } else if (url === '/clients' && Array.isArray(data)) {
                    await db.clients.clear();
                    await db.clients.bulkPut(data.map((item: any) => ({
                        id: item.id,
                        name: item.name,
                        data: item
                    })));
                } else if (url === '/company') {
                    localStorage.setItem('company_cache', JSON.stringify(data));
                } else if (url === '/dashboard/stats') {
                    localStorage.setItem('dashboard_cache', JSON.stringify(data));
                } else if (url.includes('/years')) {
                    localStorage.setItem(`years_cache_${url}`, JSON.stringify(data));
                }
            } catch (err) {
                console.error('[Cache] Failed to save data to IDB:', err);
            }

            if (Array.isArray(data) && (url === '/invoices' || url === '/offers' || url === '/clients')) {
                const merged = await appendPendingItems(data, url);
                return Promise.resolve({
                    ...response,
                    data: merged
                });
            }
        }

        // 1b. If offline but SW served cached data, merge local pending items
        if (method === 'get' && !navigator.onLine) {
            const recoveredData = await getOfflineCollectionData(url, config.params);
            if (recoveredData !== null) {
                return Promise.resolve({
                    ...response,
                    data: recoveredData,
                    status: 200,
                    statusText: 'OK_OFFLINE'
                });
            }
        }

        return response;
    },
    async (error) => {
        const config = error.config;
        const url = config.url || '';

        // 2a. HANDLE 401 UNAUTHORIZED
        if (error.response?.status === 401) {
            localStorage.removeItem(TOKEN_KEY);
            if (url !== '/auth/login' && !window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
            return Promise.reject(error);
        }

        // 2b. HANDLE OFFLINE / NETWORK ERRORS
        // 500 = server error - mos trego "U ruajt offline", por gabimin e vertete
        const isNetworkFailure = !error.response;
        const isServerError = error.response?.status >= 500;
        if (config && (isNetworkFailure || isServerError)) {
            if (isServerError) {
                // Serveri u pergjigj me gabim - mos ruaj offline, trego gabimin
                return Promise.reject(error);
            }
            console.log(`[OfflineAPI] Intercepted ${config.method} ${url} (network failure)`);

            // A) GET REQUESTS -> SERVE FROM CACHE
            if (config.method === 'get') {
                let recoveredData: any = null;

                try {
                    // --- Invoices List ---
                    if (url === '/invoices') {
                        recoveredData = await getOfflineCollectionData(url, config.params);

                        // --- Offers List ---
                    } else if (url === '/offers') {
                        recoveredData = await getOfflineCollectionData(url, config.params);

                        // --- Clients List ---
                    } else if (url === '/clients') {
                        recoveredData = await getOfflineCollectionData(url, config.params);

                        // --- Stats ---
                    } else if (url === '/dashboard/stats') {
                        const cached = localStorage.getItem('dashboard_cache');
                        recoveredData = cached ? JSON.parse(cached) : null;
                    } else if (url === '/company') {
                        const cached = localStorage.getItem('company_cache');
                        recoveredData = cached ? JSON.parse(cached) : null;
                    } else if (url.includes('/years')) {
                        const cached = localStorage.getItem(`years_cache_${url}`);
                        recoveredData = cached ? JSON.parse(cached) : null;

                        // --- NEXT NUMBER GENERATION (CRITICAL) ---
                    } else if (url === '/invoices/next-number') {
                        const local = await db.invoices.toArray();
                        const currentYear = new Date().getFullYear();

                        // Get max number from cached invoices of this year
                        let maxNum = 0;
                        local.forEach(inv => {
                            if (new Date(inv.date).getFullYear() === currentYear) {
                                // Match FATURA NR.{X} or similar
                                const match = (inv.invoice_number || '').toUpperCase().match(/NR\.(\d+)/);
                                if (match && match[1]) {
                                    const val = parseInt(match[1]);
                                    if (val > maxNum) maxNum = val;
                                }
                            }
                        });

                        // Check pending queue too!
                        const pending = OfflineService.getQueue().filter(q => q.url === '/invoices' && q.method === 'post');
                        pending.forEach(p => {
                            if (new Date(p.data.date).getFullYear() === currentYear) {
                                const match = (p.data.invoice_number || '').toUpperCase().match(/NR\.(\d+)/);
                                if (match && match[1]) {
                                    const val = parseInt(match[1]);
                                    if (val > maxNum) maxNum = val;
                                }
                            }
                        });

                        const nextNum = maxNum + 1;
                        recoveredData = { next_number: `FATURA NR.${nextNum}` };
                        console.log('[OfflineAPI] Generated Next Invoice:', recoveredData.next_number);

                    } else if (url === '/offers/next-number') {
                        const local = await db.offers.toArray();
                        // Offers are global (usually) or check pattern. Logic: Global sequence.
                        let maxNum = 0;
                        local.forEach(off => {
                            const match = (off.offer_number || '').toUpperCase().match(/NR\.(\d+)/);
                            if (match && match[1]) {
                                const val = parseInt(match[1]);
                                if (val > maxNum) maxNum = val;
                            }
                        });

                        // Check pending
                        const pending = OfflineService.getQueue().filter(q => q.url === '/offers' && q.method === 'post');
                        pending.forEach(p => {
                            const match = (p.data.offer_number || '').toUpperCase().match(/NR\.(\d+)/);
                            if (match && match[1]) {
                                const val = parseInt(match[1]);
                                if (val > maxNum) maxNum = val;
                            }
                        });

                        const nextNum = maxNum + 1;
                        recoveredData = { next_number: `OFERTA NR.${nextNum}` };
                        console.log('[OfflineAPI] Generated Next Offer:', recoveredData.next_number);
                    }

                    if (recoveredData !== null) {
                        return Promise.resolve({
                            data: recoveredData,
                            status: 200, statusText: 'OK_OFFLINE', headers: {}, config
                        });
                    }

                } catch (recoveryErr) {
                    console.error('[OfflineAPI] Recovery failed', recoveryErr);
                }
            }

            // B) MUTATION REQUESTS (POST/PUT/DELETE) -> ADD TO QUEUE
            // Accept request if it's NOT a sync-action itself
            if (['post', 'put', 'delete'].includes(config.method || '') && !config.headers?.['X-Sync-Action']) {
                let title = 'Veprim';
                if (url.includes('invoices')) title = 'Faturë';
                if (url.includes('offers')) title = 'Ofertë';
                if (config.method === 'delete') title += ' (Fshirje)';
                else title += ' (Ruajtje)';

                const action = OfflineService.addToQueue(config.method!, url, config.data, title);
                try {
                    await persistOfflineMutation(config.method!, url, config.data, action.id);
                } catch (persistErr) {
                    console.error('[OfflineAPI] Failed to persist offline mutation:', persistErr);
                }

                // Return fake success
                return Promise.resolve({
                    data: {
                        id: Math.floor(Math.random() * 1000000),
                        message: 'U ruajt offline.',
                        ...config.data
                    },
                    status: 201, statusText: 'CREATED_OFFLINE', headers: {}, config
                });
            }
        }

        return Promise.reject(error);
    }
);

// --- SERVICES EXPORT ---
export const InvoiceService = {
    getAll: (params: any) => api.get('/invoices', { params }).then(res => res.data),
    getOne: (id: number) => api.get(`/invoices/${id}`).then(res => res.data),
    getNextNumber: () => api.get('/invoices/next-number').then(res => res.data),
    getYears: () => api.get('/invoices/years').then(res => res.data),
    create: (data: any) => api.post('/invoices', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/invoices/${id}`, data).then(res => res.data),
    delete: (id: number) => api.delete(`/invoices/${id}`).then(res => res.data),
    getPdf: (id: number) => api.get(`/invoices/${id}/pdf`, { responseType: 'blob' }).then(res => res.data),
    // Alias for compatibility
    updateStatus: (id: number, status: string) => api.put(`/invoices/${id}/status`, { status }).then(res => res.data),
    toggleStatus: (id: number, status: string) => api.put(`/invoices/${id}/status`, { status }).then(res => res.data),
    bulkDelete: (ids: number[]) => api.post('/invoices/bulk-delete', { invoice_ids: ids }).then(res => res.data),
    bulkEmail: (ids: number[], email?: string) => api.post('/invoices/bulk-email', { invoice_ids: ids, override_email: email }).then(res => res.data),
    bulkEmailViaSmtp: (ids: number[], dest_email: string, company: { smtp_server?: string; smtp_port?: number; smtp_user?: string; smtp_password?: string; name?: string }) =>
        smtpApi.post('/send-bulk-email-smtp', { dest_email, document_type: 'invoice', document_ids: ids, smtp_server: company.smtp_server, smtp_port: company.smtp_port, smtp_user: company.smtp_user, smtp_password: company.smtp_password, company_name: company.name }).then(res => res.data),
    email: (id: number, dest_email?: string) => api.post(`/invoices/${id}/email`, dest_email ? { dest_email } : {}).then(res => res.data),
    emailViaSmtp: (id: number, dest_email: string, company: { smtp_server?: string; smtp_port?: number; smtp_user?: string; smtp_password?: string; name?: string }, doc?: { invoice_number?: string; date?: string; total?: number }) =>
        smtpApi.post('/send-email-smtp', { dest_email, document_type: 'invoice', document_id: id, smtp_server: company.smtp_server, smtp_port: company.smtp_port, smtp_user: company.smtp_user, smtp_password: company.smtp_password, company_name: company.name, doc_number: doc?.invoice_number, doc_date: doc?.date, doc_total: doc?.total, subject: doc ? `Faturë e re: ${doc.invoice_number} - ${company.name}` : undefined }).then(res => res.data),
};

export const OfferService = {
    getAll: (params: any) => api.get('/offers', { params }).then(res => res.data),
    getOne: (id: number) => api.get(`/offers/${id}`).then(res => res.data),
    getNextNumber: () => api.get('/offers/next-number').then(res => res.data),
    getYears: () => api.get('/offers/years').then(res => res.data),
    create: (data: any) => api.post('/offers', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/offers/${id}`, data).then(res => res.data),
    delete: (id: number) => api.delete(`/offers/${id}`).then(res => res.data),
    getPdf: (id: number) => api.get(`/offers/${id}/pdf`, { responseType: 'blob' }).then(res => res.data),
    bulkDelete: (ids: number[]) => api.post('/offers/bulk-delete', { offer_ids: ids }).then(res => res.data),
    bulkEmail: (ids: number[], email?: string) => api.post('/offers/bulk-email', { offer_ids: ids, override_email: email }).then(res => res.data),
    bulkEmailViaSmtp: (ids: number[], dest_email: string, company: { smtp_server?: string; smtp_port?: number; smtp_user?: string; smtp_password?: string; name?: string }) =>
        smtpApi.post('/send-bulk-email-smtp', { dest_email, document_type: 'offer', document_ids: ids, smtp_server: company.smtp_server, smtp_port: company.smtp_port, smtp_user: company.smtp_user, smtp_password: company.smtp_password, company_name: company.name }).then(res => res.data),
    email: (id: number, dest_email?: string) => api.post(`/offers/${id}/email`, dest_email ? { dest_email } : {}).then(res => res.data),
    emailViaSmtp: (id: number, dest_email: string, company: { smtp_server?: string; smtp_port?: number; smtp_user?: string; smtp_password?: string; name?: string }, doc?: { offer_number?: string; date?: string; total?: number }) =>
        smtpApi.post('/send-email-smtp', { dest_email, document_type: 'offer', document_id: id, smtp_server: company.smtp_server, smtp_port: company.smtp_port, smtp_user: company.smtp_user, smtp_password: company.smtp_password, company_name: company.name, doc_number: doc?.offer_number, doc_date: doc?.date, doc_total: doc?.total, subject: doc ? `Ofertë e re: ${doc.offer_number} - ${company.name}` : undefined }).then(res => res.data),
};

export const ClientService = {
    getAll: () => api.get('/clients').then(res => res.data),
    create: (data: any) => api.post('/clients', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/clients/${id}`, data).then(res => res.data),
    delete: (id: number) => api.delete(`/clients/${id}`).then(res => res.data)
};

export const CompanyService = {
    get: () => api.get('/company', { timeout: 45000 }).then(res => res.data),
    update: (data: any) => api.put('/company', data).then(res => res.data),
    uploadLogo: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/company/logo', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }).then(res => res.data);
    }
};

export const DashboardService = {
    getStats: () => api.get('/dashboard/stats', { timeout: 45000 }).then(res => res.data),
};

export const SettingsService = {
    getPaymentStatus: () => api.get('/settings/feature-payment-status').then(res => res.data),
    updatePaymentStatus: (enabled: boolean) => api.put('/settings/feature-payment-status', { enabled }).then(res => res.data),
};

export const AuthService = {
    changePassword: (currentPassword: string, newPassword: string) =>
        api.put('/auth/change-password', { current_password: currentPassword, new_password: newPassword }).then(res => res.data),
    changeUsername: (currentPassword: string, newUsername: string) =>
        api.put('/auth/change-username', { current_password: currentPassword, new_username: newUsername }).then(res => res.data),
};

export const TemplateService = {
    getAll: () => api.get('/templates').then(res => res.data),
    setDefault: (id: number) => api.put(`/templates/${id}/default`).then(res => res.data),
    toggleActive: (id: number) => api.put(`/templates/${id}/toggle-active`).then(res => res.data),
};

export default api;
