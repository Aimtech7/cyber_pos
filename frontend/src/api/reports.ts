import apiClient from './client';
import { DashboardStats } from '../types';

export const reportsApi = {
    getDashboardStats: async (): Promise<DashboardStats> => {
        const response = await apiClient.get<DashboardStats>('/reports/dashboard');
        return response.data;
    },

    getSalesReport: async (startDate: string, endDate: string): Promise<any> => {
        const response = await apiClient.post('/reports/sales', {
            start_date: startDate,
            end_date: endDate,
        });
        return response.data;
    },

    getServicePerformance: async (startDate: string, endDate: string): Promise<any> => {
        const response = await apiClient.post('/reports/services', {
            start_date: startDate,
            end_date: endDate,
        });
        return response.data;
    },

    getAttendantPerformance: async (startDate: string, endDate: string): Promise<any> => {
        const response = await apiClient.post('/reports/attendants', {
            start_date: startDate,
            end_date: endDate,
        });
        return response.data;
    },

    getProfitReport: async (startDate: string, endDate: string): Promise<any> => {
        const response = await apiClient.post('/reports/profit', {
            start_date: startDate,
            end_date: endDate,
        });
        return response.data;
    },
};
