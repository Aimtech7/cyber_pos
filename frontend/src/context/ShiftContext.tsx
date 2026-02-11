import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient as api } from '../api/client';
import { Shift } from '../types';

interface ShiftContextType {
    currentShift: Shift | null;
    loading: boolean;
    refreshShift: () => Promise<void>;
    openShift: (amount: number) => Promise<void>;
    closeShift: (countedCash: number, notes?: string) => Promise<void>;
}

const ShiftContext = createContext<ShiftContextType | undefined>(undefined);

export const ShiftProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentShift, setCurrentShift] = useState<Shift | null>(null);
    const [loading, setLoading] = useState(true);

    const refreshShift = async () => {
        try {
            const response = await api.get<Shift>('/shifts/current');
            setCurrentShift(response.data);
        } catch (error) {
            console.error('Error fetching current shift:', error);
            setCurrentShift(null);
        } finally {
            setLoading(false);
        }
    };

    const openShift = async (openingCash: number) => {
        await api.post('/shifts/open', { opening_cash: openingCash });
        await refreshShift();
    };

    const closeShift = async (countedCash: number, notes?: string) => {
        await api.post('/shifts/close', { counted_cash: countedCash, close_notes: notes });
        await refreshShift();
    };

    useEffect(() => {
        refreshShift();
    }, []);

    return (
        <ShiftContext.Provider value={{ currentShift, loading, refreshShift, openShift, closeShift }}>
            {children}
        </ShiftContext.Provider>
    );
};

export const useShift = () => {
    const context = useContext(ShiftContext);
    if (!context) {
        throw new Error('useShift must be used within a ShiftProvider');
    }
    return context;
};
