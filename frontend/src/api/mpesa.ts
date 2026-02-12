import apiClient from './client';

export interface PaymentIntentCreate {
    transaction_id: string;
    phone_number: string;
    amount: number;
}

export interface PaymentIntentResponse {
    id: string;
    transaction_id: string;
    amount: number;
    phone_number: string;
    status: 'pending' | 'confirmed' | 'failed' | 'expired' | 'cancelled';
    mpesa_checkout_request_id?: string;
    mpesa_receipt_number?: string;
    failure_reason?: string;
    created_at: string;
    expires_at: string;
    confirmed_at?: string;
    is_expired: boolean;
    is_pending: boolean;
}

export interface STKPushResponse {
    payment_intent_id: string;
    checkout_request_id: string;
    merchant_request_id: string;
    response_code: string;
    response_description: string;
    customer_message: string;
}

export interface MpesaPayment {
    id: string;
    mpesa_receipt_number: string;
    amount: number;
    phone_number: string;
    transaction_date: string;
    sender_name?: string;
    is_matched: boolean;
    matched_transaction_id?: string;
    matched_at?: string;
    created_at: string;
}

export interface MpesaInboxResponse {
    items: MpesaPayment[];
    total: number;
    page: number;
    page_size: number;
    unmatched_count: number;
    unmatched_total: number;
}

export interface ReconciliationReport {
    date: string;
    expected_mpesa_count: number;
    expected_mpesa_total: number;
    confirmed_count: number;
    confirmed_total: number;
    unmatched_count: number;
    unmatched_total: number;
    failed_count: number;
    failed_total: number;
    expired_count: number;
    expired_total: number;
    variance_amount: number;
    variance_percentage: number;
    unmatched_payments: MpesaPayment[];
    failed_intents: PaymentIntentResponse[];
}

/**
 * Initiate M-Pesa STK Push payment
 */
export const initiatePayment = async (data: PaymentIntentCreate): Promise<STKPushResponse> => {
    const response = await apiClient.post('/mpesa/initiate', data);
    return response.data;
};

/**
 * Check payment intent status
 */
export const checkPaymentStatus = async (intentId: string): Promise<PaymentIntentResponse> => {
    const response = await apiClient.get(`/mpesa/intent/${intentId}`);
    return response.data;
};

/**
 * Get M-Pesa inbox (all payments)
 */
export const getMpesaInbox = async (params?: {
    page?: number;
    page_size?: number;
    is_matched?: boolean;
    date_from?: string;
    date_to?: string;
}): Promise<MpesaInboxResponse> => {
    const response = await apiClient.get('/mpesa/inbox', { params });
    return response.data;
};

/**
 * Get potential matches for unmatched payment
 */
export const getPotentialMatches = async (mpesaPaymentId: string) => {
    const response = await apiClient.get(`/mpesa/potential-matches/${mpesaPaymentId}`);
    return response.data;
};

/**
 * Manually match M-Pesa payment to transaction
 */
export const matchPayment = async (data: {
    mpesa_payment_id: string;
    transaction_id: string;
    notes?: string;
}) => {
    const response = await apiClient.post('/mpesa/match', data);
    return response.data;
};

/**
 * Get reconciliation report
 */
export const getReconciliationReport = async (date?: string): Promise<ReconciliationReport> => {
    const params = date ? { report_date: date } : {};
    const response = await apiClient.get('/mpesa/reconciliation', { params });
    return response.data;
};
