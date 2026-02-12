import apiClient from './client';
import { Transaction, TransactionItem } from '../types';

export const transactionsApi = {
    list: async (): Promise<Transaction[]> => {
        const response = await apiClient.get<Transaction[]>('/transactions/');
        return response.data;
    },

    get: async (id: string): Promise<Transaction> => {
        const response = await apiClient.get<Transaction>(`/transactions/${id}`);
        return response.data;
    },

    create: async (data: {
        items: TransactionItem[];
        payment_method: 'cash' | 'mpesa' | 'account';
        mpesa_code?: string;
        customer_id?: string;
        discount_amount?: number;
    }): Promise<Transaction> => {
        const response = await apiClient.post<Transaction>('/transactions/', data);
        return response.data;
    },

    getReceipt: async (id: string): Promise<Blob> => {
        const response = await apiClient.get(`/transactions/${id}/receipt`, {
            responseType: 'blob',
        });
        return response.data;
    },

    void: async (id: string, reason: string): Promise<void> => {
        await apiClient.post(`/transactions/${id}/void`, { reason });
    },

    refund: async (id: string, reason: string): Promise<void> => {
        await apiClient.post(`/transactions/${id}/refund`, { reason });
    },
};
