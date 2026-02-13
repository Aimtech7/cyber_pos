import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useShift } from '../../context/ShiftContext';
import { reportsApi } from '../../api/reports';
import { DashboardStats } from '../../types';
import { DollarSign, ShoppingCart, Monitor, LogOut, Plus, List, Lock, Unlock, History } from 'lucide-react';
import ShiftModal from '../../components/ShiftModal';

const POSDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const { currentShift, loading: shiftLoading } = useShift();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [showShiftModal, setShowShiftModal] = useState(false);
    const [modalMode, setModalMode] = useState<'open' | 'close'>('open');

    useEffect(() => {
        loadData();
    }, [currentShift]);

    const loadData = async () => {
        try {
            const dashboardStats = await reportsApi.getDashboardStats();
            setStats(dashboardStats);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    const handleOpenShiftClick = () => {
        setModalMode('open');
        setShowShiftModal(true);
    };

    const handleCloseShiftClick = () => {
        setModalMode('close');
        setShowShiftModal(true);
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
                {!shiftLoading && (
                    !currentShift ? (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6 flex flex-col items-center text-center">
                            <Lock className="w-12 h-12 text-yellow-500 mb-2" />
                            <h2 className="text-xl font-bold text-yellow-900 mb-2">Shift is Closed</h2>
                            <p className="text-yellow-700 mb-4 max-w-md">
                                You must open a shift to start making sales and tracking cash.
                            </p>
                            <button onClick={handleOpenShiftClick} className="btn btn-primary px-8 py-2 text-lg">
                                Open Shift
                            </button>
                        </div>
                    ) : (
                        <div className="bg-white border-l-4 border-green-500 shadow-sm rounded-r-lg p-6 mb-6">
                            <div className="flex justify-between items-start">
                                <div className="flex items-start gap-4">
                                    <div className="bg-green-100 p-2 rounded-full">
                                        <Unlock className="w-6 h-6 text-green-600" />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-bold text-gray-900">Active Shift</h2>
                                        <div className="mt-1 text-sm text-gray-600 space-y-1">
                                            <p><span className="font-medium">Started:</span> {new Date(currentShift.opened_at).toLocaleString()}</p>
                                            <p><span className="font-medium">Opening Cash:</span> KES {currentShift.opening_cash}</p>
                                            <p><span className="font-medium">Total Sales:</span> KES {currentShift.total_sales}</p>
                                        </div>
                                    </div>
                                </div>
                                <button onClick={handleCloseShiftClick} className="btn btn-danger">
                                    Close Shift
                                </button>
                            </div>
                        </div>
                    )
                )}

                {/* Functionality Blocked Message */}
                {!currentShift && !shiftLoading && (
                    <div className="mb-8 opacity-50 pointer-events-none filter grayscale">
                        <div className="absolute inset-0 z-10"></div>
                        {/* We overlay this on the stats/actions to visually disable them */}
                    </div>
                )}

                <div className={!currentShift ? "opacity-50 pointer-events-none filter grayscale transition-all duration-300" : ""}>
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
                            className="card hover:shadow-lg transition-shadow cursor-pointer flex items-center gap-4 p-6"
                        >
                            <div className="bg-primary-100 p-4 rounded-full">
                                <Plus className="w-8 h-8 text-primary-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-900">New Sale</h3>
                                <p className="text-gray-600">Create a new sale transaction</p>
                            </div>
                        </Link>

                        <Link
                            to="/pos/sessions"
                            className="card hover:shadow-lg transition-shadow cursor-pointer flex items-center gap-4 p-6"
                        >
                            <div className="bg-blue-100 p-4 rounded-full">
                                <List className="w-8 h-8 text-blue-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-900">Computer Sessions</h3>
                                <p className="text-gray-600">Manage computer usage & billing</p>
                            </div>
                        </Link>
                    </div>


                    <Link
                        to="/pos/transactions"
                        className="card hover:shadow-lg transition-shadow cursor-pointer flex items-center gap-4 p-6"
                    >
                        <div className="bg-purple-100 p-4 rounded-full">
                            <History className="w-8 h-8 text-purple-600" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-900">History</h3>
                            <p className="text-gray-600">View past transactions & receipts</p>
                        </div>
                    </Link>
                </div>

            </main >

            <ShiftModal
                isOpen={showShiftModal}
                onClose={() => setShowShiftModal(false)}
                mode={modalMode}
            />
        </div >
    );
};

export default POSDashboard;
