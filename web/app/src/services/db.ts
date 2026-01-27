import Dexie, { Table } from 'dexie';

export interface LocalInvoice {
    id?: number;
    cloudId?: number;
    invoice_number: string;
    date: string;
    total: number;
    data: any; // Full object storage
    last_sync: number;
}

export interface LocalOffer {
    id?: number;
    cloudId?: number;
    offer_number: string;
    date: string;
    total: number;
    data: any;
    last_sync: number;
}

export interface LocalClient {
    id?: number;
    cloudId?: number;
    name: string;
    data: any;
    last_sync: number;
}

export class HolkosDB extends Dexie {
    invoices!: Table<LocalInvoice>;
    offers!: Table<LocalOffer>;
    clients!: Table<LocalClient>;

    constructor() {
        super('HolkosBackup');
        // Version 2 to handle schema change from ++id to id
        this.version(2).stores({
            invoices: 'id, invoice_number, date',
            offers: 'id, offer_number, date',
            clients: 'id, name'
        });
    }
}

export const db = new HolkosDB();
