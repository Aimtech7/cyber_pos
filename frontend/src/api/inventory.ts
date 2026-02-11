import { apiClient } from './client';

export interface InventoryItem {
    id: string;
    name: string;
    unit: string;
    current_stock: number;
    min_stock_level: number;
    unit_cost: number;
    created_at: string;
    updated_at: string;
}

export interface StockMovement {
    id: string;
    item_id: string;
    movement_type: 'purchase' | 'usage' | 'adjustment';
    quantity: number;
    reference_id?: string;
    notes?: string;
    created_by: string;
    created_at: string;
}

export const inventoryApi = {
    getAll: async (lowStockOnly = false) => {
        const response = await apiClient.get<InventoryItem[]>('/inventory', {
            params: { low_stock_only: lowStockOnly }
        });
        return response.data;
    },

    getLowStock: async () => {
        const response = await apiClient.get<InventoryItem[]>('/inventory/low-stock');
        return response.data;
    },

    create: async (data: Partial<InventoryItem>) => {
        const response = await apiClient.post<InventoryItem>('/inventory', data);
        return response.data;
    },

    update: async (id: string, data: Partial<InventoryItem>) => {
        const response = await apiClient.patch<InventoryItem>(`/inventory/${id}`, data);
        return response.data;
    },

    adjustStock: async (data: { item_id: string; movement_type: string; quantity: number; notes?: string }) => {
        const response = await apiClient.post<StockMovement>('/inventory/movements', data);
        return response.data;
    },

    getMovements: async (itemId: string) => {
        const response = await apiClient.get<StockMovement[]>(`/inventory/movements/${itemId}`);
        return response.data;
    }
};
