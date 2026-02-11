import apiClient from './client';
import { Service } from '../types';

export const servicesApi = {
    list: async (activeOnly = true): Promise<Service[]> => {
        const response = await apiClient.get<Service[]>('/services/', {
            params: { active_only: activeOnly },
        });
        return response.data;
    },

    get: async (id: string): Promise<Service> => {
        const response = await apiClient.get<Service>(`/services/${id}`);
        return response.data;
    },

    create: async (data: Partial<Service>): Promise<Service> => {
        const response = await apiClient.post<Service>('/services/', data);
        return response.data;
    },

    update: async (id: string, data: Partial<Service>): Promise<Service> => {
        const response = await apiClient.patch<Service>(`/services/${id}`, data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/services/${id}`);
    },
};
