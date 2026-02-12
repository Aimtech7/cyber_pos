import apiClient from './client';

// Alert Types
export type AlertType = 'void_abuse' | 'discount_abuse' | 'cash_discrepancy' | 'inventory_manipulation' | 'price_tampering';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertStatus = 'open' | 'acknowledged' | 'resolved';

export interface Alert {
    id: string;
    type: AlertType;
    severity: AlertSeverity;
    status: AlertStatus;
    message: string;
    description?: string;
    related_entity?: {
        type: string;
        id: string;
        name?: string;
        user_id?: string;
        user_name?: string;
    };
    metadata?: Record<string, any>;
    assigned_to?: string;
    acknowledged_by?: string;
    acknowledged_at?: string;
    resolved_by?: string;
    resolved_at?: string;
    resolution_notes?: string;
    created_at: string;
    updated_at: string;
}

export interface AlertListResponse {
    items: Alert[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

export interface AlertStats {
    total_open: number;
    total_acknowledged: number;
    total_resolved: number;
    by_severity: Record<string, number>;
    by_type: Record<string, number>;
    critical_open: number;
    high_open: number;
}

export interface AlertAcknowledge {
    notes?: string;
}

export interface AlertResolve {
    resolution_notes: string;
}

export interface AlertUpdate {
    assigned_to?: string;
}

export const alertsApi = {
    list: async (params?: {
        page?: number;
        page_size?: number;
        type_filter?: AlertType;
        severity_filter?: AlertSeverity;
        status_filter?: AlertStatus;
    }): Promise<AlertListResponse> => {
        const queryParams = new URLSearchParams();
        if (params?.page) queryParams.append('page', params.page.toString());
        if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
        if (params?.type_filter) queryParams.append('type_filter', params.type_filter);
        if (params?.severity_filter) queryParams.append('severity_filter', params.severity_filter);
        if (params?.status_filter) queryParams.append('status_filter', params.status_filter);

        const response = await apiClient.get<AlertListResponse>(`/alerts?${queryParams.toString()}`);
        return response.data;
    },

    getStats: async (): Promise<AlertStats> => {
        const response = await apiClient.get<AlertStats>('/alerts/stats');
        return response.data;
    },

    get: async (id: string): Promise<Alert> => {
        const response = await apiClient.get<Alert>(`/alerts/${id}`);
        return response.data;
    },

    acknowledge: async (id: string, data: AlertAcknowledge): Promise<Alert> => {
        const response = await apiClient.post<Alert>(`/alerts/${id}/acknowledge`, data);
        return response.data;
    },

    resolve: async (id: string, data: AlertResolve): Promise<Alert> => {
        const response = await apiClient.post<Alert>(`/alerts/${id}/resolve`, data);
        return response.data;
    },

    update: async (id: string, data: AlertUpdate): Promise<Alert> => {
        const response = await apiClient.put<Alert>(`/alerts/${id}`, data);
        return response.data;
    },

    runChecks: async (): Promise<{ success: boolean; alerts_created: number; message: string }> => {
        const response = await apiClient.post('/alerts/run-checks');
        return response.data;
    },
};
