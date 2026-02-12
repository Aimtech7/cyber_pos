/**
 * Offline Storage Service using IndexedDB
 * Manages pending transactions queue for offline mode
 */

const DB_NAME = 'cybercafe_pos_offline';
const DB_VERSION = 1;
const STORE_NAME = 'pending_transactions';

export interface PendingTransaction {
    id: string;  // Local UUID
    client_generated_id: string;  // UUID for idempotency
    offline_receipt_number: string;  // OFF-YYYYMMDD-xxxx
    transaction_data: {
        items: Array<{
            service_id?: string;
            session_id?: string;
            description: string;
            quantity: number;
            unit_price: number;
        }>;
        payment_method: string;
        mpesa_code?: string;
        customer_id?: string;
        discount_amount?: number;
    };
    created_at: string;  // ISO timestamp
    status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED';
    retry_count: number;
    last_error?: string;
    synced_transaction_id?: string;  // Official transaction ID after sync
    synced_receipt_number?: number;  // Official receipt number after sync
}

class OfflineStorageService {
    private db: IDBDatabase | null = null;
    private initPromise: Promise<void> | null = null;

    /**
     * Initialize IndexedDB
     */
    async init(): Promise<void> {
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('IndexedDB failed to open:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('IndexedDB initialized successfully');
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result;

                // Create object store if it doesn't exist
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    const objectStore = db.createObjectStore(STORE_NAME, { keyPath: 'id' });

                    // Create indexes
                    objectStore.createIndex('client_generated_id', 'client_generated_id', { unique: true });
                    objectStore.createIndex('status', 'status', { unique: false });
                    objectStore.createIndex('created_at', 'created_at', { unique: false });
                    objectStore.createIndex('offline_receipt_number', 'offline_receipt_number', { unique: false });

                    console.log('Object store created with indexes');
                }
            };
        });

        return this.initPromise;
    }

    /**
     * Ensure DB is initialized
     */
    private async ensureDB(): Promise<IDBDatabase> {
        if (!this.db) {
            await this.init();
        }
        if (!this.db) {
            throw new Error('Failed to initialize IndexedDB');
        }
        return this.db;
    }

    /**
     * Add transaction to queue
     */
    async addTransaction(transaction: PendingTransaction): Promise<void> {
        const db = await this.ensureDB();

        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const request = store.add(transaction);

            request.onsuccess = () => {
                console.log('Transaction added to offline queue:', transaction.offline_receipt_number);
                resolve();
            };

            request.onerror = () => {
                console.error('Failed to add transaction:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get all pending transactions (PENDING or FAILED status)
     */
    async getPendingTransactions(): Promise<PendingTransaction[]> {
        const db = await this.ensureDB();

        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const store = tx.objectStore(STORE_NAME);
            const index = store.index('status');

            const transactions: PendingTransaction[] = [];

            // Get PENDING transactions
            const pendingRequest = index.getAll('PENDING');
            pendingRequest.onsuccess = () => {
                transactions.push(...pendingRequest.result);

                // Get FAILED transactions
                const failedRequest = index.getAll('FAILED');
                failedRequest.onsuccess = () => {
                    transactions.push(...failedRequest.result);

                    // Sort by created_at (FIFO)
                    transactions.sort((a, b) =>
                        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                    );

                    resolve(transactions);
                };

                failedRequest.onerror = () => reject(failedRequest.error);
            };

            pendingRequest.onerror = () => reject(pendingRequest.error);
        });
    }

    /**
     * Get all transactions (any status)
     */
    async getAllTransactions(): Promise<PendingTransaction[]> {
        const db = await this.ensureDB();

        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const store = tx.objectStore(STORE_NAME);
            const request = store.getAll();

            request.onsuccess = () => {
                const transactions = request.result;
                // Sort by created_at
                transactions.sort((a, b) =>
                    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                );
                resolve(transactions);
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Update transaction status
     */
    async updateTransaction(id: string, updates: Partial<PendingTransaction>): Promise<void> {
        const db = await this.ensureDB();

        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const getRequest = store.get(id);

            getRequest.onsuccess = () => {
                const transaction = getRequest.result;
                if (!transaction) {
                    reject(new Error('Transaction not found'));
                    return;
                }

                const updated = { ...transaction, ...updates };
                const putRequest = store.put(updated);

                putRequest.onsuccess = () => resolve();
                putRequest.onerror = () => reject(putRequest.error);
            };

            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    /**
     * Remove transaction from queue
     */
    async removeTransaction(id: string): Promise<void> {
        const db = await this.ensureDB();

        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const request = store.delete(id);

            request.onsuccess = () => {
                console.log('Transaction removed from queue:', id);
                resolve();
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Clear all transactions
     */
    async clearAll(): Promise<void> {
        const db = await this.ensureDB();

        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const request = store.clear();

            request.onsuccess = () => {
                console.log('All transactions cleared');
                resolve();
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get pending count
     */
    async getPendingCount(): Promise<number> {
        const pending = await this.getPendingTransactions();
        return pending.length;
    }

    /**
     * Generate offline receipt number
     * Format: OFF-YYYYMMDD-xxxx
     */
    generateOfflineReceiptNumber(): string {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const random = String(Math.floor(Math.random() * 10000)).padStart(4, '0');

        return `OFF-${year}${month}${day}-${random}`;
    }
}

// Export singleton instance
export const offlineStorage = new OfflineStorageService();
