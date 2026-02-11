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

                {/* Analytics Grid */}
                {stats && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                        {/* Recent Activity */}
                        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-bold text-gray-900">Recent Activity</h3>
                                <Link to="/admin/reports" className="text-sm text-primary-600 hover:text-primary-700">View All</Link>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            <th className="pb-3">Time</th>
                                            <th className="pb-3">Transaction</th>
                                            <th className="pb-3">Status</th>
                                            <th className="pb-3 text-right">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {stats.recent_transactions?.map((tx) => (
                                            <tr key={tx.id}>
                                                <td className="py-3 text-sm text-gray-600">{tx.time}</td>
                                                <td className="py-3 text-sm font-medium text-gray-900">#{tx.transaction_number}</td>
                                                <td className="py-3">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-semibold
                                                        ${tx.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                            tx.status === 'voided' ? 'bg-red-100 text-red-800' :
                                                                'bg-orange-100 text-orange-800'}`}>
                                                        {tx.status}
                                                    </span>
                                                </td>
                                                <td className="py-3 text-sm font-bold text-gray-900 text-right">
                                                    KES {tx.amount.toFixed(2)}
                                                </td>
                                            </tr>
                                        ))}
                                        {(!stats.recent_transactions || stats.recent_transactions.length === 0) && (
                                            <tr>
                                                <td colSpan={4} className="py-4 text-center text-gray-500">No recent activity</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Side Widgets */}
                        <div className="space-y-6">
                            {/* Payment Breakdown */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-bold text-gray-900 mb-4">Payments Today</h3>
                                <div className="space-y-4">
                                    {stats.payment_breakdown?.map((item) => (
                                        <div key={item.method} className="flex justify-between items-center">
                                            <div>
                                                <p className="font-medium text-gray-900 capitalize">{item.method}</p>
                                                <p className="text-xs text-gray-500">{item.count} transactions</p>
                                            </div>
                                            <p className="font-bold text-gray-900">KES {item.amount.toFixed(2)}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Top Services */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-bold text-gray-900 mb-4">Top Services</h3>
                                <div className="space-y-4">
                                    {stats.top_services?.map((service, idx) => (
                                        <div key={idx} className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-gray-700 truncate w-32" title={service.service_name}>
                                                {service.service_name}
                                            </span>
                                            <div className="text-right">
                                                <p className="text-sm font-bold text-gray-900">KES {service.revenue.toFixed(0)}</p>
                                                <p className="text-xs text-gray-500">{service.quantity_sold} sold</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
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

                    <Link
                        to="/admin/inventory"
                        className="card hover:shadow-lg transition-shadow cursor-pointer"
                    >
                        <div className="flex items-center gap-4">
                            <div className="bg-orange-100 p-4 rounded-lg">
                                <Package className="w-8 h-8 text-orange-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-gray-900">Inventory</h3>
                                <p className="text-gray-600">Manage stock & items</p>
                            </div>
                        </div>
                    </Link>

                    {user?.role === 'ADMIN' && (
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
