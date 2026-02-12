/**
 * Network Status Detection Service
 * Monitors online/offline status and connection quality
 */

type NetworkStatusListener = (isOnline: boolean) => void;

class NetworkStatusService {
    private listeners: Set<NetworkStatusListener> = new Set();
    private isOnline: boolean = navigator.onLine;
    private checkInterval: number | null = null;

    constructor() {
        this.init();
    }

    /**
     * Initialize network status monitoring
     */
    private init(): void {
        // Listen to browser online/offline events
        window.addEventListener('online', this.handleOnline);
        window.addEventListener('offline', this.handleOffline);

        // Periodic connectivity check (every 30 seconds)
        this.startPeriodicCheck();
    }

    /**
     * Handle online event
     */
    private handleOnline = (): void => {
        console.log('Network: ONLINE');
        this.isOnline = true;
        this.notifyListeners(true);
    };

    /**
     * Handle offline event
     */
    private handleOffline = (): void => {
        console.log('Network: OFFLINE');
        this.isOnline = false;
        this.notifyListeners(false);
    };

    /**
     * Start periodic connectivity check
     */
    private startPeriodicCheck(): void {
        this.checkInterval = window.setInterval(() => {
            this.checkConnectivity();
        }, 30000); // Check every 30 seconds
    }

    /**
     * Check actual connectivity by making a request
     */
    private async checkConnectivity(): Promise<boolean> {
        try {
            // Try to fetch a small resource from the backend
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

            const response = await fetch('/health', {
                method: 'GET',
                signal: controller.signal,
                cache: 'no-cache'
            });

            clearTimeout(timeoutId);

            const isOnline = response.ok;

            // Update status if changed
            if (isOnline !== this.isOnline) {
                this.isOnline = isOnline;
                this.notifyListeners(isOnline);
            }

            return isOnline;
        } catch (error) {
            // Network error - we're offline
            if (this.isOnline) {
                this.isOnline = false;
                this.notifyListeners(false);
            }
            return false;
        }
    }

    /**
     * Notify all listeners of status change
     */
    private notifyListeners(isOnline: boolean): void {
        this.listeners.forEach(listener => {
            try {
                listener(isOnline);
            } catch (error) {
                console.error('Error in network status listener:', error);
            }
        });
    }

    /**
     * Add listener for network status changes
     */
    addListener(listener: NetworkStatusListener): () => void {
        this.listeners.add(listener);

        // Return unsubscribe function
        return () => {
            this.listeners.delete(listener);
        };
    }

    /**
     * Get current online status
     */
    getStatus(): boolean {
        return this.isOnline;
    }

    /**
     * Force check connectivity now
     */
    async forceCheck(): Promise<boolean> {
        return await this.checkConnectivity();
    }

    /**
     * Cleanup
     */
    destroy(): void {
        window.removeEventListener('online', this.handleOnline);
        window.removeEventListener('offline', this.handleOffline);

        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }

        this.listeners.clear();
    }
}

// Export singleton instance
export const networkStatus = new NetworkStatusService();
