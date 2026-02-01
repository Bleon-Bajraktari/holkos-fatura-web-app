import axios from 'axios';
import { db } from './db';

export interface PendingAction {
    id: string; // Unique GUID for the action
    method: string;
    url: string;
    data: any;
    timestamp: number;
    title: string;
    status: 'pending' | 'syncing' | 'error';
    error?: string;
}

const QUEUE_KEY = 'offline_pending_actions';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

// Dedicated axios instance for syncing to avoid circular dependency with api.ts
// and to bypass the main interceptors that might requeue the request.
const syncApi = axios.create({
    baseURL: API_BASE
});

const buildTempId = (actionId: string) => `temp-${actionId}`;

const getEntityFromUrl = (url: string) => {
    const match = url.match(/\/(invoices|offers|clients)(?:\/([^/?]+))?/i);
    if (!match) return null;
    return {
        entity: match[1].toLowerCase() as 'invoices' | 'offers' | 'clients',
        id: match[2]
    };
};

const updateQueuedClientReferences = async (tempId: string, finalId: string | number, clientName?: string) => {
    const queue = OfflineService.getQueue();
    let changed = false;
    const updatedQueue = queue.map(action => {
        if (action.data?.client_id === tempId) {
            changed = true;
            return {
                ...action,
                data: {
                    ...action.data,
                    client_id: finalId,
                    client: clientName ? { name: clientName } : action.data?.client
                }
            };
        }
        return action;
    });
    if (changed) {
        OfflineService.saveQueue(updatedQueue);
    }

    const updateLocalDocs = async (tableName: 'invoices' | 'offers') => {
        const table = (db as any)[tableName];
        const records = await table.toArray();
        await Promise.all(records.map(async (record: any) => {
            if (record?.data?.client_id === tempId) {
                const nextData = {
                    ...record.data,
                    client_id: finalId,
                    client: clientName ? { name: clientName } : record.data?.client
                };
                await table.put({
                    ...record,
                    data: nextData
                });
            }
        }));
    };

    await updateLocalDocs('invoices');
    await updateLocalDocs('offers');
};

const applySyncedResult = async (action: PendingAction, responseData: any) => {
    const info = getEntityFromUrl(action.url);
    if (!info) return;

    const { entity, id } = info;
    const tempId = buildTempId(action.id);
    const data = responseData && typeof responseData === 'object'
        ? { ...action.data, ...responseData }
        : action.data;
    const cleanedData = data ? { ...data } : {};
    delete cleanedData._isOfflinePending;

    if (action.method === 'post') {
        const finalId = cleanedData.id ?? id ?? tempId;
        if (entity === 'invoices') {
            await db.invoices.delete(tempId as any);
            await db.invoices.put({
                id: finalId as any,
                invoice_number: cleanedData.invoice_number,
                date: cleanedData.date,
                data: cleanedData
            });
        } else if (entity === 'offers') {
            await db.offers.delete(tempId as any);
            await db.offers.put({
                id: finalId as any,
                offer_number: cleanedData.offer_number,
                date: cleanedData.date,
                data: cleanedData
            });
        } else if (entity === 'clients') {
            await db.clients.delete(tempId as any);
            await db.clients.put({
                id: finalId as any,
                name: cleanedData.name,
                data: cleanedData
            });
            await updateQueuedClientReferences(tempId, finalId, cleanedData.name);
        }
        return;
    }

    if (action.method === 'put') {
        if (!id) return;
        if (entity === 'invoices') {
            const existing = await db.invoices.get(id as any);
            const mergedData = { ...(existing?.data || {}), ...cleanedData, id: existing?.data?.id ?? id };
            await db.invoices.put({
                id: id as any,
                invoice_number: mergedData.invoice_number || existing?.invoice_number || '',
                date: mergedData.date || existing?.date || new Date().toISOString(),
                data: mergedData
            });
        } else if (entity === 'offers') {
            const existing = await db.offers.get(id as any);
            const mergedData = { ...(existing?.data || {}), ...cleanedData, id: existing?.data?.id ?? id };
            await db.offers.put({
                id: id as any,
                offer_number: mergedData.offer_number || existing?.offer_number || '',
                date: mergedData.date || existing?.date || new Date().toISOString(),
                data: mergedData
            });
        } else if (entity === 'clients') {
            const existing = await db.clients.get(id as any);
            const mergedData = { ...(existing?.data || {}), ...cleanedData, id: existing?.data?.id ?? id };
            await db.clients.put({
                id: id as any,
                name: mergedData.name || existing?.name || '',
                data: mergedData
            });
        }
        return;
    }

    if (action.method === 'delete' && id) {
        if (entity === 'invoices') await db.invoices.delete(id as any);
        if (entity === 'offers') await db.offers.delete(id as any);
        if (entity === 'clients') await db.clients.delete(id as any);
    }
};

export const OfflineService = {
    // 1. Get current queue
    getQueue(): PendingAction[] {
        try {
            const stored = localStorage.getItem(QUEUE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            return [];
        }
    },

    // 2. Add an item to the queue
    addToQueue(method: string, url: string, data: any, title: string) {
        const queue = this.getQueue();
        const newAction: PendingAction = {
            id: Math.random().toString(36).substr(2, 9) + Date.now().toString(36),
            method,
            url,
            data,
            timestamp: Date.now(),
            title,
            status: 'pending'
        };
        queue.push(newAction);
        this.saveQueue(queue);
        window.dispatchEvent(new Event('offline_queue_changed'));
        return newAction;
    },

    // 3. Update an action status
    updateAction(id: string, updates: Partial<PendingAction>) {
        const queue = this.getQueue().map(a => a.id === id ? { ...a, ...updates } : a);
        this.saveQueue(queue);
        window.dispatchEvent(new Event('offline_queue_changed'));
    },

    // 4. Remove an action (success or cancel)
    removeFromQueue(id: string) {
        const queue = this.getQueue().filter(a => a.id !== id);
        this.saveQueue(queue);
        window.dispatchEvent(new Event('offline_queue_changed'));
    },

    // 5. Remove pending document by temp ID (fshirje lokale e faturave/ofertave offline)
    async removePendingDocument(entity: 'invoices' | 'offers' | 'clients', tempId: string) {
        const actionId = String(tempId).replace(/^temp-/, '');
        const queue = this.getQueue();
        const action = queue.find(a => a.id === actionId && getEntityFromUrl(a.url)?.entity === entity);
        if (action) this.removeFromQueue(actionId);
        if (entity === 'invoices') await db.invoices.delete(tempId as any);
        if (entity === 'offers') await db.offers.delete(tempId as any);
        if (entity === 'clients') await db.clients.delete(tempId as any);
    },

    saveQueue(queue: PendingAction[]) {
        localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
    },

    // 5. The Sync Loop
    async sync() {
        if (!navigator.onLine) {
            console.log('[Sync] Offline. Stopping sync.');
            return;
        }

        const queue = this.getQueue().filter(a => a.status !== 'error' && a.status !== 'syncing');
        if (queue.length === 0) return;

        console.log(`[Sync] Starting sync for ${queue.length} items...`);

        for (const action of queue) {
            try {
                this.updateAction(action.id, { status: 'syncing' });

                // Use the dedicated syncApi
                const response = await syncApi({
                    method: action.method,
                    url: action.url,
                    data: action.data
                });
                try {
                    await applySyncedResult(action, response?.data);
                } catch (persistErr) {
                    console.error('[Sync] Failed to persist synced data:', persistErr);
                }

                console.log(`[Sync] Action ${action.id} completed.`);
                this.removeFromQueue(action.id);

                // Notify UI
                window.dispatchEvent(new CustomEvent('offline_sync_completed', { detail: action }));

            } catch (error: any) {
                console.error(`[Sync] Action ${action.id} failed:`, error);

                const errorMessage = error.response?.data?.detail || error.message || 'Unknown Error';
                const isClientError = error.response && error.response.status >= 400 && error.response.status < 500;

                if (isClientError) {
                    // Fatal Validation Error (e.g. Duplicate Number). Mark as error so user can fix.
                    this.updateAction(action.id, {
                        status: 'error',
                        error: errorMessage
                    });
                    window.dispatchEvent(new CustomEvent('offline_sync_error', { detail: { ...action, error: errorMessage } }));
                } else {
                    // Server/Network Error. Reset to pending to retry later.
                    this.updateAction(action.id, { status: 'pending' });
                    // Provide a small delay to avoid hammering
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
        }
    }
};
