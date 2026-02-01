import Dexie, { Table } from 'dexie';

export interface LocalInvoice {
    id?: number | string; // IndexedDB internal ID (auto-incremented or mapped from backend ID)
    invoice_number: string;
    date: string;
    data: any; // Full JSON data
}

export interface LocalOffer {
    id?: number | string;
    offer_number: string;
    date: string;
    data: any;
}

export interface LocalClient {
    id?: number | string;
    name: string;
    data: any; // Full client data
}

export class HolkosDB extends Dexie {
    invoices!: Table<LocalInvoice>;
    offers!: Table<LocalOffer>;
    clients!: Table<LocalClient>;

    constructor() {
        super('HolkosBackup');
        // Define simple schema for querying/sorting
        // Storing the full object in 'data' avoids schema migration headaches
        this.version(2).stores({
            // SHËNIM: 'data' nuk shkruhet këtu sepse nuk është index kërkimi,
            // por ajo RUHET automatikisht bashkë me objektin.
            invoices: 'id, invoice_number, date',
            offers: 'id, offer_number, date',
            clients: 'id, name'
        });
    }
}

export const db = new HolkosDB();
