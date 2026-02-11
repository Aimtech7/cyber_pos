import apiClient from './client';
import { Shift } from '../types';

export const shiftsApi = {
    list: async (): Promise<Shift[]> => {
        const response = await apiClient.get<Shift[]>('/shifts/');
        return response.data;
    },

    getCurrent: async (): Promise<Shift | null> => {
        const response = await apiClient.get<Shift | null>('/shifts/current');
        return response.data;
    },

    open: async (openingCash: number): Promise<Shift> => {
        const response = await apiClient.post<Shift>('/shifts/open', {
            opening_cash: openingCash,
        });
        return response.data;
    },

    close: async (countedCash: number): Promise<Shift> => {
        const response = await apiClient.post<Shift>('/shifts/close', {
            counted_cash: countedCash,
        });
        return response.data;
    },
};
