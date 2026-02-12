/**
 * Offline Context Provider
 * Global state management for offline mode
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { offlineStorage } from '../services/offlineStorage';
import { networkStatus } from '../services/networkStatus';
import { syncEngine } from '../services/syncEngine';

interface OfflineContextType {
    isOnline: boolean;
    pendingCount: number;
    isSyncing: boolean;
    syncProgress: {
        synced: number;
        failed: number;
        total: number;
    } | null;
    refreshPendingCount: () => Promise<void>;
    manualSync: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export const useOffline = (): OfflineContextType => {
    const context = useContext(OfflineContext);
    if (!context) {
        throw new Error('useOffline must be used within OfflineProvider');
    }
    return context;
};

interface OfflineProviderProps {
    children: ReactNode;
}

export const OfflineProvider: React.FC<OfflineProviderProps> = ({ children }) => {
    const [isOnline, setIsOnline] = useState(networkStatus.getStatus());
    const [pendingCount, setPendingCount] = useState(0);
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState<{
        synced: number;
        failed: number;
        total: number;
    } | null>(null);

    // Load pending count on mount
    useEffect(() => {
        refreshPendingCount();
    }, []);

    // Listen to network status changes
    useEffect(() => {
        const unsubscribe = networkStatus.addListener((online) => {
            setIsOnline(online);
        });

        return unsubscribe;
    }, []);

    // Listen to sync events
    useEffect(() => {
        const unsubscribe = syncEngine.addEventListener((event) => {
            switch (event.type) {
                case 'sync_started':
                    setIsSyncing(true);
                    setSyncProgress({ synced: 0, failed: 0, total: event.data.count });
                    break;

                case 'sync_progress':
                    setSyncProgress(event.data);
                    break;

                case 'sync_completed':
                case 'sync_failed':
                    setIsSyncing(false);
                    setSyncProgress(null);
                    refreshPendingCount();
                    break;

                case 'transaction_synced':
                    refreshPendingCount();
                    break;
            }
        });

        return unsubscribe;
    }, []);

    const refreshPendingCount = async () => {
        try {
            const count = await offlineStorage.getPendingCount();
            setPendingCount(count);
        } catch (error) {
            console.error('Failed to refresh pending count:', error);
        }
    };

    const manualSync = async () => {
        try {
            await syncEngine.manualSync();
        } catch (error) {
            console.error('Manual sync failed:', error);
        }
    };

    const value: OfflineContextType = {
        isOnline,
        pendingCount,
        isSyncing,
        syncProgress,
        refreshPendingCount,
        manualSync,
    };

    return <OfflineContext.Provider value={value}>{children}</OfflineContext.Provider>;
};
