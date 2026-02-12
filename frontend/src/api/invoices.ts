import { client } from './client';

export interface Invoice {
    id: string;
    invoice_number: string;
    customer_id: string;
    status: 'draft' | 'issued' | 'part_paid' | 'paid' | 'overdue' | 'cancelled';
    issue_date?: string;
    due_date?: string;
    subtotal: number;
    tax_amount: number;
    total_amount: number;
    paid_amount: number;
    balance: number;
    notes?: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    is_overdue: boolean;
    days_overdue: number;
    items: InvoiceItem[];
}

export interface InvoiceItem {
    id: string;
    invoice_id: string;
    transaction_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    total_price: number;
}

export interface InvoiceCreate {
    customer_id: string;
    items: {
        transaction_id?: string;
        description: string;
        quantity: number;
        unit_price: number;
        total_price: number;
    }[];
    due_days?: number;
    notes?: string;
    issue_immediately?: boolean;
}

export interface InvoiceListResponse {
    items: Invoice[];
    total: number;
    page: number;
    page_size: number;
}

export interface InvoicePayment {
    id: string;
    invoice_id: string;
    payment_date: string;
    amount: number;
    payment_method: 'cash' | 'mpesa' | 'bank_transfer';
    reference?: string;
    notes?: string;
    recorded_by: string;
    created_at: string;
}

export interface InvoicePaymentCreate {
    amount: number;
    payment_method: 'cash' | 'mpesa' | 'bank_transfer';
    reference?: string;
    notes?: string;
}

export interface AgingReportResponse {
    customer_id?: string;
    customer_name?: string;
    buckets: {
        [key: string]: {
            range_label: string;
            count: number;
            total_amount: number;
        };
    };
    total_outstanding: number;
    total_invoices: number;
}

export const invoicesApi = {
    /**
     * Create new invoice
     */
    create: async (data: InvoiceCreate): Promise<Invoice> => {
        const response = await client.post('/invoices', data);
        return response.data;
    },

    /**
     * Create invoice from transactions
     */
    createFromTransactions: async (data: {
        customer_id: string;
        transaction_ids: string[];
        due_days?: number;
        notes?: string;
        issue_immediately?: boolean;
    }): Promise<Invoice> => {
        const response = await client.post('/invoices/from-transactions', data);
        return response.data;
    },

    /**
     * List invoices
     */
    list: async (params?: {
        page?: number;
        page_size?: number;
        customer_id?: string;
        status_filter?: string;
        overdue_only?: boolean;
    }): Promise<InvoiceListResponse> => {
        const response = await client.get('/invoices', { params });
        return response.data;
    },

    /**
     * Get invoice details
     */
    get: async (id: string): Promise<Invoice> => {
        const response = await client.get(`/invoices/${id}`);
        return response.data;
    },

    /**
     * Update invoice
     */
    update: async (id: string, data: { due_date?: string; notes?: string }): Promise<Invoice> => {
        const response = await client.put(`/invoices/${id}`, data);
        return response.data;
    },

    /**
     * Issue invoice (DRAFT → ISSUED)
     */
    issue: async (id: string): Promise<Invoice> => {
        const response = await client.post(`/invoices/${id}/issue`, {});
        return response.data;
    },

    /**
     * Cancel invoice
     */
    cancel: async (id: string, reason?: string): Promise<Invoice> => {
        const response = await client.post(`/invoices/${id}/cancel`, { reason });
        return response.data;
    },

    /**
     * Record payment
     */
    recordPayment: async (id: string, data: InvoicePaymentCreate): Promise<InvoicePayment> => {
        const response = await client.post(`/invoices/${id}/payments`, data);
        return response.data;
    },

    /**
     * List invoice payments
     */
    listPayments: async (id: string): Promise<InvoicePayment[]> => {
        const response = await client.get(`/invoices/${id}/payments`);
        return response.data;
    },

    /**
     * Get aging report
     */
    getAgingReport: async (customer_id?: string): Promise<AgingReportResponse[]> => {
        const response = await client.get('/invoices/aging-report', {
            params: customer_id ? { customer_id } : {},
        });
        return response.data;
    },
};
