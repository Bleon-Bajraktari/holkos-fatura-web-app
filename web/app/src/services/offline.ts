import api from './api';

export interface PendingAction {
    id: string;
    method: string;
    url: string;
    data: any;
    timestamp: number;
    title: string;
    status: 'pending' | 'syncing' | 'error';
    error?: string;
}

const QUEUE_KEY = 'offline_pending_actions';

export const OfflineService = {
    getQueue(): PendingAction[] {
        const stored = localStorage.getItem(QUEUE_KEY);
        return stored ? JSON.parse(stored) : [];
    },

    addToQueue(method: string, url: string, data: any, title: string) {
        const queue = this.getQueue();
        const newAction: PendingAction = {
            id: Math.random().toString(36).substr(2, 9),
            method,
            url,
            data,
            timestamp: Date.now(),
            title,
            status: 'pending'
        };
        queue.push(newAction);
        localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
        return newAction;
    },

    updateAction(id: string, updates: Partial<PendingAction>) {
        const queue = this.getQueue().map(a => a.id === id ? { ...a, ...updates } : a);
        localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
    },

    removeFromQueue(id: string) {
        const queue = this.getQueue().filter(a => a.id !== id);
        localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
    },

    async sync() {
        if (!navigator.onLine) return;

        const queue = this.getQueue().filter(a => a.status !== 'error'); // Provojmë vetëm ato që s'kanë gabim
        if (queue.length === 0) return;

        for (const action of queue) {
            try {
                this.updateAction(action.id, { status: 'syncing' });

                await api({
                    method: action.method,
                    url: action.url,
                    data: action.data,
                    headers: { 'X-Sync-Action': 'true' }
                });

                this.removeFromQueue(action.id);
                window.dispatchEvent(new CustomEvent('offline_sync_completed', { detail: action }));
            } catch (error: any) {
                const errorMessage = error.response?.data?.detail || 'Gabim gjatë sinkronizimit';

                // Nëse është gabim 4xx (p.sh. Duplikim numri), e markojmë si Gabim
                if (error.response && error.response.status >= 400 && error.response.status < 500) {
                    this.updateAction(action.id, {
                        status: 'error',
                        error: errorMessage
                    });
                    window.dispatchEvent(new CustomEvent('offline_sync_error', { detail: { ...action, error: errorMessage } }));
                } else {
                    // Për gabime serveri (500) ose rrjeti, thjesht e kthejmë në pending për ta provuar prapë
                    this.updateAction(action.id, { status: 'pending' });
                }
                break;
            }
        }
    }
};
