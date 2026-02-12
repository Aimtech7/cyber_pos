/**
 * Sync Engine Service
 * Handles automatic synchronization of offline transactions with exponential backoff
 */

import { offlineStorage, PendingTransaction } from './offlineStorage';
import { networkStatus } from './networkStatus';
import { transactionsApi } from '../api/transactions';

const MAX_RETRIES = 5;
const BACKOFF_BASE_MS = 1000; // 1 second
const SYNC_INTERVAL_MS = 5000; // Check every 5 seconds when online

type SyncEventType = 'sync_started' | 'sync_progress' | 'sync_completed' | 'sync_failed' | 'transaction_synced' | 'transaction_failed';

interface SyncEvent {
    type: SyncEventType;
    data?: any;
}

type SyncEventListener = (event: SyncEvent) => void;

class SyncEngineService {
    private isSyncing: boolean = false;
    private syncInterval: number | null = null;
    private listeners: Set<SyncEventListener> = new Set();
    private networkUnsubscribe: (() => void) | null = null;

    constructor() {
        this.init();
    }

    /**
     * Initialize sync engine
     */
    private async init(): Promise<void> {
        // Initialize offline storage
        await offlineStorage.init();

        // Listen to network status changes
        this.networkUnsubscribe = networkStatus.addListener((isOnline) => {
            if (isOnline) {
                console.log('Network restored - starting sync');
                this.startAutoSync();
            } else {
                console.log('Network lost - stopping sync');
                this.stopAutoSync();
            }
        });

        // Start auto-sync if online
        if (networkStatus.getStatus()) {
            this.startAutoSync();
        }
    }

    /**
     * Start automatic sync interval
     */
    private startAutoSync(): void {
        if (this.syncInterval) {
            return; // Already running
        }

        // Sync immediately
        this.syncPendingTransactions();

        // Then sync periodically
        this.syncInterval = window.setInterval(() => {
            this.syncPendingTransactions();
        }, SYNC_INTERVAL_MS);

        console.log('Auto-sync started');
    }

    /**
     * Stop automatic sync
     */
    private stopAutoSync(): void {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
            console.log('Auto-sync stopped');
        }
    }

    /**
     * Sync all pending transactions
     */
    async syncPendingTransactions(): Promise<void> {
        if (this.isSyncing) {
            console.log('Sync already in progress, skipping');
            return;
        }

        if (!networkStatus.getStatus()) {
            console.log('Offline - skipping sync');
            return;
        }

        const pending = await offlineStorage.getPendingTransactions();

        if (pending.length === 0) {
            return; // Nothing to sync
        }

        console.log(`Starting sync of ${pending.length} transactions`);
        this.isSyncing = true;
        this.emitEvent({ type: 'sync_started', data: { count: pending.length } });

        let synced = 0;
        let failed = 0;

        for (const transaction of pending) {
            try {
                await this.syncTransaction(transaction);
                synced++;
                this.emitEvent({
                    type: 'transaction_synced',
                    data: {
                        offlineReceipt: transaction.offline_receipt_number,
                        progress: { synced, total: pending.length }
                    }
                });
            } catch (error) {
                failed++;
                console.error(`Failed to sync transaction ${transaction.offline_receipt_number}:`, error);
                this.emitEvent({
                    type: 'transaction_failed',
                    data: {
                        offlineReceipt: transaction.offline_receipt_number,
                        error: error instanceof Error ? error.message : 'Unknown error'
                    }
                });
            }

            // Emit progress
            this.emitEvent({
                type: 'sync_progress',
                data: { synced, failed, total: pending.length }
            });
        }

        this.isSyncing = false;

        if (failed === 0) {
            console.log(`Sync completed successfully: ${synced} transactions`);
            this.emitEvent({ type: 'sync_completed', data: { synced, failed } });
        } else {
            console.log(`Sync completed with errors: ${synced} synced, ${failed} failed`);
            this.emitEvent({ type: 'sync_failed', data: { synced, failed } });
        }
    }

    /**
     * Sync a single transaction with retry logic
     */
    private async syncTransaction(transaction: PendingTransaction): Promise<void> {
        // Update status to SYNCING
        await offlineStorage.updateTransaction(transaction.id, { status: 'SYNCING' });

        let lastError: Error | null = null;

        for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
            try {
                // Attempt to create transaction on server
                const response = await transactionsApi.create({
                    ...transaction.transaction_data,
                    payment_method: transaction.transaction_data.payment_method as 'cash' | 'mpesa' | 'account',
                    client_generated_id: transaction.client_generated_id,
                    offline_receipt_number: transaction.offline_receipt_number
                });

                // Success! Update local record
                await offlineStorage.updateTransaction(transaction.id, {
                    status: 'SYNCED',
                    synced_transaction_id: response.id,
                    synced_receipt_number: response.transaction_number,
                    retry_count: attempt
                });

                console.log(`Transaction synced: ${transaction.offline_receipt_number} -> #${response.transaction_number}`);

                // Remove from queue after successful sync
                await offlineStorage.removeTransaction(transaction.id);

                return; // Success!

            } catch (error) {
                lastError = error instanceof Error ? error : new Error('Unknown error');
                console.error(`Sync attempt ${attempt + 1} failed:`, lastError.message);

                // If this is not the last attempt, wait with exponential backoff
                if (attempt < MAX_RETRIES) {
                    const backoffMs = BACKOFF_BASE_MS * Math.pow(2, attempt);
                    console.log(`Retrying in ${backoffMs}ms...`);
                    await this.sleep(backoffMs);
                }
            }
        }

        // All retries failed - mark as FAILED
        await offlineStorage.updateTransaction(transaction.id, {
            status: 'FAILED',
            retry_count: MAX_RETRIES,
            last_error: lastError?.message || 'Unknown error'
        });

        throw lastError || new Error('Sync failed after all retries');
    }

    /**
     * Sleep utility
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Add event listener
     */
    addEventListener(listener: SyncEventListener): () => void {
        this.listeners.add(listener);

        // Return unsubscribe function
        return () => {
            this.listeners.delete(listener);
        };
    }

    /**
     * Emit event to all listeners
     */
    private emitEvent(event: SyncEvent): void {
        this.listeners.forEach(listener => {
            try {
                listener(event);
            } catch (error) {
                console.error('Error in sync event listener:', error);
            }
        });
    }

    /**
     * Manual sync trigger
     */
    async manualSync(): Promise<void> {
        console.log('Manual sync triggered');
        await this.syncPendingTransactions();
    }

    /**
     * Get sync status
     */
    isSyncInProgress(): boolean {
        return this.isSyncing;
    }

    /**
     * Cleanup
     */
    destroy(): void {
        this.stopAutoSync();

        if (this.networkUnsubscribe) {
            this.networkUnsubscribe();
        }

        this.listeners.clear();
    }
}

// Export singleton instance
export const syncEngine = new SyncEngineService();
