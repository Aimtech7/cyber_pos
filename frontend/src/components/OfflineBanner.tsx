/**
 * Offline Banner Component
 * Displays offline status and sync progress
 */

import React from 'react';
import { WifiOff, RefreshCw, CheckCircle, AlertCircle, Wifi } from 'lucide-react';
import { useOffline } from '../context/OfflineContext';

export const OfflineBanner: React.FC = () => {
    const { isOnline, pendingCount, isSyncing, syncProgress, manualSync } = useOffline();

    // Don't show banner if online and no pending transactions
    if (isOnline && pendingCount === 0 && !isSyncing) {
        return null;
    }

    return (
        <div className={`fixed top-0 left-0 right-0 z-50 ${isOnline ? 'bg-blue-600' : 'bg-orange-600'
            } text-white shadow-lg`}>
            <div className="max-w-7xl mx-auto px-4 py-3">
                <div className="flex items-center justify-between">
                    {/* Status */}
                    <div className="flex items-center gap-3">
                        {isOnline ? (
                            <Wifi className="w-5 h-5" />
                        ) : (
                            <WifiOff className="w-5 h-5 animate-pulse" />
                        )}

                        <div>
                            <div className="font-semibold">
                                {isOnline ? (
                                    isSyncing ? 'Syncing...' : 'Online - Syncing Pending Transactions'
                                ) : (
                                    'Offline Mode'
                                )}
                            </div>
                            <div className="text-sm opacity-90">
                                {isSyncing && syncProgress ? (
                                    `${syncProgress.synced} of ${syncProgress.total} synced${syncProgress.failed > 0 ? `, ${syncProgress.failed} failed` : ''
                                    }`
                                ) : (
                                    `${pendingCount} transaction${pendingCount !== 1 ? 's' : ''} pending sync`
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3">
                        {/* Sync Progress */}
                        {isSyncing && syncProgress && (
                            <div className="flex items-center gap-2">
                                <RefreshCw className="w-4 h-4 animate-spin" />
                                <span className="text-sm">
                                    {Math.round((syncProgress.synced / syncProgress.total) * 100)}%
                                </span>
                            </div>
                        )}

                        {/* Manual Sync Button */}
                        {isOnline && !isSyncing && pendingCount > 0 && (
                            <button
                                onClick={manualSync}
                                className="px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-sm font-medium transition-colors"
                            >
                                Sync Now
                            </button>
                        )}

                        {/* Status Icons */}
                        {!isSyncing && (
                            <>
                                {syncProgress && syncProgress.failed > 0 ? (
                                    <AlertCircle className="w-5 h-5" />
                                ) : pendingCount === 0 ? (
                                    <CheckCircle className="w-5 h-5" />
                                ) : null}
                            </>
                        )}
                    </div>
                </div>

                {/* Progress Bar */}
                {isSyncing && syncProgress && (
                    <div className="mt-2 bg-white bg-opacity-20 rounded-full h-1 overflow-hidden">
                        <div
                            className="bg-white h-full transition-all duration-300"
                            style={{ width: `${(syncProgress.synced / syncProgress.total) * 100}%` }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};
