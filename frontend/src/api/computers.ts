import apiClient from './client';
import { Computer, Session } from '../types';

export const computersApi = {
    list: async (): Promise<Computer[]> => {
        const response = await apiClient.get<Computer[]>('/computers/');
        return response.data;
    },

    get: async (id: string): Promise<Computer> => {
        const response = await apiClient.get<Computer>(`/computers/${id}`);
        return response.data;
    },
};

export const sessionsApi = {
    list: async (activeOnly = false): Promise<Session[]> => {
        const response = await apiClient.get<Session[]>('/sessions/', {
            params: { active_only: activeOnly },
        });
        return response.data;
    },

    start: async (computerId: string): Promise<Session> => {
        const response = await apiClient.post<Session>('/sessions/start', {
            computer_id: computerId,
        });
        return response.data;
    },

    stop: async (sessionId: string): Promise<Session> => {
        const response = await apiClient.post<Session>('/sessions/stop', {
            session_id: sessionId,
        });
        return response.data;
    },
};
