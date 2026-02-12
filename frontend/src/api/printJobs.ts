import { client } from './client';

export interface PrintJob {
    id: string;
    job_number: string;
    computer_id: string;
    requested_by: string;
    description?: string;
    pages_bw: number;
    pages_color: number;
    total_pages: number;
    total_amount: number;
    status: 'pending' | 'approved' | 'rejected' | 'printed' | 'cancelled';
    transaction_id?: string;
    approved_by?: string;
    approved_at?: string;
    rejected_by?: string;
    rejected_at?: string;
    rejection_reason?: string;
    printed_by?: string;
    printed_at?: string;
    created_at: string;
    updated_at: string;
}

export interface PrintJobCreate {
    computer_id: string;
    requested_by: string;
    description?: string;
    pages_bw: number;
    pages_color: number;
}

export interface PrintJobListResponse {
    items: PrintJob[];
    total: number;
    page: number;
    page_size: number;
    pending_count: number;
    approved_count: number;
}

export interface PrintJobStats {
    total_jobs: number;
    pending_jobs: number;
    approved_jobs: number;
    printed_jobs: number;
    rejected_jobs: number;
    cancelled_jobs: number;
    total_revenue: number;
    total_pages_bw: number;
    total_pages_color: number;
}

export const printJobsApi = {
    /**
     * Submit a new print job
     */
    submit: async (data: PrintJobCreate): Promise<PrintJob> => {
        const response = await client.post('/print-jobs', data);
        return response.data;
    },

    /**
     * List print jobs with optional filtering
     */
    list: async (params?: {
        page?: number;
        page_size?: number;
        status_filter?: string;
        computer_id?: string;
    }): Promise<PrintJobListResponse> => {
        const response = await client.get('/print-jobs', { params });
        return response.data;
    },

    /**
     * Get print job details
     */
    get: async (id: string): Promise<PrintJob> => {
        const response = await client.get(`/print-jobs/${id}`);
        return response.data;
    },

    /**
     * Approve print job
     */
    approve: async (id: string): Promise<PrintJob> => {
        const response = await client.post(`/print-jobs/${id}/approve`, {});
        return response.data;
    },

    /**
     * Reject print job
     */
    reject: async (id: string, rejection_reason: string): Promise<PrintJob> => {
        const response = await client.post(`/print-jobs/${id}/reject`, {
            rejection_reason,
        });
        return response.data;
    },

    /**
     * Mark job as printed
     */
    markPrinted: async (id: string): Promise<PrintJob> => {
        const response = await client.post(`/print-jobs/${id}/mark-printed`, {});
        return response.data;
    },

    /**
     * Cancel print job
     */
    cancel: async (id: string): Promise<PrintJob> => {
        const response = await client.post(`/print-jobs/${id}/cancel`);
        return response.data;
    },

    /**
     * Get print job statistics
     */
    getStats: async (): Promise<PrintJobStats> => {
        const response = await client.get('/print-jobs/stats/summary');
        return response.data;
    },
};
