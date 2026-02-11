export interface User {
    id: string;
    username: string;
    email: string;
    full_name: string;
    role: 'admin' | 'manager' | 'attendant';
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface Service {
    id: string;
    name: string;
    pricing_mode: 'per_page' | 'per_minute' | 'per_job' | 'bundle';
    base_price: number;
    description?: string;
    is_active: boolean;
    requires_stock: boolean;
    stock_item_id?: string;
}

export interface Computer {
    id: string;
    name: string;
    status: 'available' | 'in_use' | 'offline' | 'maintenance';
    current_session_id?: string;
}

export interface Session {
    id: string;
    computer_id: string;
    started_by: string;
    start_time: string;
    end_time?: string;
    duration_minutes?: number;
    amount_charged?: number;
    transaction_id?: string;
    status: 'active' | 'completed' | 'cancelled';
}

export interface TransactionItem {
    id?: string;
    service_id?: string;
    session_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    total_price?: number;
}

export interface Transaction {
    id: string;
    transaction_number: number;
    created_by: string;
    shift_id: string;
    total_amount: number;
    discount_amount: number;
    final_amount: number;
    payment_method: 'cash' | 'mpesa';
    mpesa_code?: string;
    status: 'completed' | 'voided' | 'refunded';
    created_at: string;
    items: TransactionItem[];
}

export interface Shift {
    id: string;
    user_id: string;
    opened_at: string;
    closed_at?: string;
    opening_cash: number;
    expected_cash?: number;
    counted_cash?: number;
    cash_difference?: number;
    total_sales: number;
    total_mpesa: number;
    status: 'open' | 'closed';
}

export interface InventoryItem {
    id: string;
    name: string;
    unit: string;
    current_stock: number;
    min_stock_level: number;
    unit_cost: number;
}

export interface Expense {
    id: string;
    category: 'rent' | 'utilities' | 'repairs' | 'supplies' | 'other';
    description: string;
    amount: number;
    expense_date: string;
    recorded_by: string;
}

export interface DashboardStats {
    today_sales: number;
    today_transactions: number;
    active_sessions: number;
    low_stock_items: number;
    available_computers: number;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}
