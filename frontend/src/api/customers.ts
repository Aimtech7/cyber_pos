import { client } from './client';

export interface Customer {
    id: string;
    customer_number: string;
    name: string;
    phone?: string;
    email?: string;
    type: 'individual' | 'institution';
    notes?: string;
    credit_limit: number;
    current_balance: number;
    available_credit: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface CustomerCreate {
    name: string;
    phone?: string;
    email?: string;
    type: 'individual' | 'institution';
    notes?: string;
    credit_limit?: number;
}

export interface CustomerUpdate {
    name?: string;
    phone?: string;
    email?: string;
    type?: 'individual' | 'institution';
    notes?: string;
    credit_limit?: number;
    is_active?: boolean;
}

export interface CustomerListResponse {
    items: Customer[];
    total: number;
    page: number;
    page_size: number;
}

export interface CreditCheckResponse {
    customer_id: string;
    customer_name: string;
    credit_limit: number;
    current_balance: number;
    available_credit: number;
    requested_amount: number;
    can_proceed: boolean;
    message: string;
}

export const customersApi = {
    /**
     * Create new customer
     */
    create: async (data: CustomerCreate): Promise<Customer> => {
        const response = await client.post('/customers', data);
        return response.data;
    },

    /**
     * List customers
     */
    list: async (params?: {
        page?: number;
        page_size?: number;
        search?: string;
        type_filter?: string;
        active_only?: boolean;
    }): Promise<CustomerListResponse> => {
        const response = await client.get('/customers', { params });
        return response.data;
    },

    /**
     * Get customer details
     */
    get: async (id: string): Promise<Customer> => {
        const response = await client.get(`/customers/${id}`);
        return response.data;
    },

    /**
     * Update customer
     */
    update: async (id: string, data: CustomerUpdate): Promise<Customer> => {
        const response = await client.put(`/customers/${id}`, data);
        return response.data;
    },

    /**
     * Deactivate customer
     */
    deactivate: async (id: string): Promise<Customer> => {
        const response = await client.post(`/customers/${id}/deactivate`);
        return response.data;
    },

    /**
     * Check credit availability
     */
    checkCredit: async (id: string, amount: number): Promise<CreditCheckResponse> => {
        const response = await client.post(`/customers/${id}/check-credit`, { amount });
        return response.data;
    },

    /**
     * Get customer statement
     */
    getStatement: async (id: string) => {
        const response = await client.get(`/customers/${id}/statement`);
        return response.data;
    },
};
