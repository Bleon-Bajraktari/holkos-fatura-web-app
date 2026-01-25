import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
});

export const InvoiceService = {
    getAll: () => api.get('/invoices').then(res => res.data),
    getOne: (id: number) => api.get(`/invoices/${id}`).then(res => res.data),
    create: (data: any) => api.post('/invoices', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/invoices/${id}`, data).then(res => res.data),
    delete: (id: number) => api.delete(`/invoices/${id}`).then(res => res.data),
    email: (id: number) => api.post(`/invoices/${id}/email`).then(res => res.data),
};

export const OfferService = {
    getAll: () => api.get('/offers').then(res => res.data),
    getOne: (id: number) => api.get(`/offers/${id}`).then(res => res.data),
    create: (data: any) => api.post('/offers', data).then(res => res.data),
    update: (id: number, data: any) => api.put(`/offers/${id}`, data).then(res => res.data),
    getNextNumber: () => api.get('/offers/next-number').then(res => res.data),
    email: (id: number) => api.post(`/offers/${id}/email`).then(res => res.data),
};

export const ClientService = {
    getAll: () => api.get('/clients').then(res => res.data),
    create: (data: any) => api.post('/clients', data).then(res => res.data),
};

export const CompanyService = {
    get: () => api.get('/company').then(res => res.data),
    update: (data: any) => api.put('/company', data).then(res => res.data),
};

export const DashboardService = {
    getStats: () => api.get('/dashboard/stats').then(res => res.data),
};

export default api;
