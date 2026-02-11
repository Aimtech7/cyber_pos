import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { shiftsApi } from '../../api/shifts';
import { reportsApi } from '../../api/reports';
import { Shift, DashboardStats } from '../../types';
import { DollarSign, ShoppingCart, Monitor, LogOut, Plus, List } from 'lucide-react';

const POSDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const [currentShift, setCurrentShift] = useState<Shift | null>(null);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [showOpenShift, setShowOpenShift] = useState(false);
    const [openingCash, setOpeningCash] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [shift, dashboardStats] = await Promise.all([
                shiftsApi.getCurrent(),
                reportsApi.getDashboardStats(),
            ]);
            setCurrentShift(shift);
            setStats(dashboardStats);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    const handleOpenShift = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const shift = await shiftsApi.open(parseFloat(openingCash));
            setCurrentShift(shift);
            setShowOpenShift(false);
            setOpeningCash('');
        } catch (error) {
            console.error('Error opening shift:', error);
            alert('Failed to open shift');
        }
    };

    const handleCloseShift = async () => {
        if (!currentShift) return;

        const countedCash = prompt('Enter counted cash amount:');
        if (countedCash) {
            try {
                await shiftsApi.close(parseFloat(countedCash));
                setCurrentShift(null);
                loadData();
            } catch (error) {
                console.error('Error closing shift:', error);
                alert('Failed to close shift');
            }
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">POS Dashboard</h1>
                            <p className="text-sm text-gray-600">Welcome, {user?.full_name}</p>
                        </div>
                        <button onClick={logout} className="btn btn-secondary flex items-center gap-2">
                            <LogOut className="w-4 h-4" />
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Shift Status */}
                {!currentShift ? (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                        <h2 className="text-lg font-semibold text-yellow-900 mb-2">No Active Shift</h2>
                        <p className="text-yellow-700 mb-4">You need to open a shift before making sales.</p>
                        {!showOpenShift ? (
                            <button onClick={() => setShowOpenShift(true)} className="btn btn-primary">
                                Open Shift
                            </button>
                        ) : (
                            <form onSubmit={handleOpenShift} className="flex gap-4 items-end">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Opening Cash Amount
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={openingCash}
                                        onChange={(e) => setOpeningCash(e.target.value)}
                                        className="input"
                                        placeholder="0.00"
                                        required
                                    />
                                </div>
                                <button type="submit" className="btn btn-primary">Open Shift</button>
                                <button
                                    type="button"
                                    onClick={() => setShowOpenShift(false)}
                                    className="btn btn-secondary"
                                >
                                    Cancel
                                </button>
                            </form>
                        )}
                    </div>
                ) : (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                        <div className="flex justify-between items-start">
                            <div>
                                <h2 className="text-lg font-semibold text-green-900 mb-2">Active Shift</h2>
                                <p className="text-green-700">Opened: {new Date(currentShift.opened_at).toLocaleString()}</p>
                                <p className="text-green-700">Opening Cash: KES {currentShift.opening_cash.toFixed(2)}</p>
                                <p className="text-green-700">Total Sales: KES {currentShift.total_sales.toFixed(2)}</p>
                            </div>
                            <button onClick={handleCloseShift} className="btn btn-danger">
                                Close Shift
                            </button>
                        </div>
                    </div>
                )}

                {/* Stats Grid */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Today's Sales</p>
                                    <p className="text-2xl font-bold text-gray-900">
                                        KES {stats.today_sales.toFixed(2)}
                                    </p>
                                </div>
                                <DollarSign className="w-12 h-12 text-primary-600" />
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Transactions</p>
                                    <p className="text-2xl font-bold text-gray-900">{stats.today_transactions}</p>
                                </div>
                                <ShoppingCart className="w-12 h-12 text-green-600" />
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Active Sessions</p>
                                    <p className="text-2xl font-bold text-gray-900">{stats.active_sessions}</p>
                                </div>
                                <Monitor className="w-12 h-12 text-blue-600" />
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600">Available PCs</p>
                                    <p className="text-2xl font-bold text-gray-900">{stats.available_computers}</p>
                                </div>
                                <Monitor className="w-12 h-12 text-purple-600" />
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Link
                        to="/pos/new-sale"
                        className="card hover:shadow-lg transition-shadow cursor-pointer"
                    >
                        <div className="flex items-center gap-4">
                            <div className="bg-primary-100 p-4 rounded-lg">
                                <Plus className="w-8 h-8 text-primary-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-gray-900">New Sale</h3>
                                <p className="text-gray-600">Create a new transaction</p>
                            </div>
                        </div>
                    </Link>

                    <Link
                        to="/pos/sessions"
                        className="card hover:shadow-lg transition-shadow cursor-pointer"
                    >
                        <div className="flex items-center gap-4">
                            <div className="bg-blue-100 p-4 rounded-lg">
                                <List className="w-8 h-8 text-blue-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-gray-900">Computer Sessions</h3>
                                <p className="text-gray-600">Manage PC sessions</p>
                            </div>
                        </div>
                    </Link>
                </div>
            </main>
        </div>
    );
};

export default POSDashboard;
