import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { reportsApi } from '../../api/reports';
import { DashboardStats } from '../../types';
import { DollarSign, ShoppingCart, Monitor, Package, LogOut, Settings, Users, FileText } from 'lucide-react';

const AdminDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState<DashboardStats | null>(null);

    useEffect(() => {
        loadStats();
        const interval = setInterval(loadStats, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const loadStats = async () => {
        try {
            const data = await reportsApi.getDashboardStats();
            setStats(data);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
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
                {/* Stats Grid */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
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
                                    <p className="text-sm text-gray-600">Low Stock Items</p>
                                    <p className="text-2xl font-bold text-gray-900">{stats.low_stock_items}</p>
                                </div>
                                <Package className="w-12 h-12 text-orange-600" />
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

                {/* Quick Links */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <Link
                        to="/admin/services"
                        className="card hover:shadow-lg transition-shadow cursor-pointer"
                    >
                        <div className="flex items-center gap-4">
                            <div className="bg-primary-100 p-4 rounded-lg">
                                <Settings className="w-8 h-8 text-primary-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-gray-900">Services</h3>
                                <p className="text-gray-600">Manage services & pricing</p>
                            </div>
                        </div>
                    </Link>

                    {user?.role === 'admin' && (
                        <Link
                            to="/admin/users"
                            className="card hover:shadow-lg transition-shadow cursor-pointer"
                        >
                            <div className="flex items-center gap-4">
                                <div className="bg-blue-100 p-4 rounded-lg">
                                    <Users className="w-8 h-8 text-blue-600" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold text-gray-900">Users</h3>
                                    <p className="text-gray-600">Manage users & roles</p>
                                </div>
                            </div>
                        </Link>
                    )}

                    <Link
                        to="/admin/reports"
                        className="card hover:shadow-lg transition-shadow cursor-pointer"
                    >
                        <div className="flex items-center gap-4">
                            <div className="bg-green-100 p-4 rounded-lg">
                                <FileText className="w-8 h-8 text-green-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-gray-900">Reports</h3>
                                <p className="text-gray-600">View analytics & reports</p>
                            </div>
                        </div>
                    </Link>
                </div>
            </main>
        </div>
    );
};

export default AdminDashboard;
