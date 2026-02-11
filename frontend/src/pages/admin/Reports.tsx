import React, { useState } from 'react';
import { reportsApi } from '../../api/reports';
import { useAuth } from '../../context/AuthContext';
import { Download, Calendar, Filter } from 'lucide-react';
import { Transaction } from '../../types';

const Reports: React.FC = () => {
    const { user } = useAuth();
    const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'transactions' | 'sales'>('transactions');
    const [summary, setSummary] = useState<any>(null);

    const handleSearch = async () => {
        setLoading(true);
        try {
            if (activeTab === 'transactions') {
                const data = await reportsApi.getTransactions(startDate, endDate);
                setTransactions(data);
            } else if (activeTab === 'sales') {
                const data = await reportsApi.getSalesReport(startDate, endDate);
                setSummary(data);
            }
        } catch (error) {
            console.error('Error fetching details:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await reportsApi.exportTransactions(startDate, endDate);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transactions_${startDate}_${endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error exporting:', error);
            alert('Failed to export transactions');
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Reports & Analytics</h1>

            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow mb-6 flex flex-wrap gap-4 items-end">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="input"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="input"
                    />
                </div>
                <button
                    onClick={handleSearch}
                    className="btn btn-primary flex items-center gap-2"
                    disabled={loading}
                >
                    <Filter size={18} />
                    Generate Report
                </button>
                <div className="flex-1 text-right">
                    <button
                        onClick={handleExport}
                        className="btn btn-secondary flex items-center gap-2 ml-auto"
                        title="Export filtered transactions to CSV"
                    >
                        <Download size={18} />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gray-200 mb-6">
                <button
                    className={`pb-2 px-4 font-medium ${activeTab === 'transactions' ? 'text-primary-600 border-b-2 border-primary-600' : 'text-gray-500'}`}
                    onClick={() => setActiveTab('transactions')}
                >
                    Transactions List
                </button>
                <button
                    className={`pb-2 px-4 font-medium ${activeTab === 'sales' ? 'text-primary-600 border-b-2 border-primary-600' : 'text-gray-500'}`}
                    onClick={() => setActiveTab('sales')}
                >
                    Sales Summary
                </button>
            </div>

            {/* Content */}
            <div className="bg-white rounded-lg shadow overflow-hidden min-h-[400px]">
                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="text-gray-500">Loading data...</div>
                    </div>
                ) : activeTab === 'transactions' ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attendant</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {transactions.length === 0 ? (
                                    <tr><td colSpan={6} className="p-8 text-center text-gray-500">No transactions found for this period</td></tr>
                                ) : (
                                    transactions.map((t: any) => (
                                        <tr key={t.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(t.created_at).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 font-medium">#{t.transaction_number}</td>
                                            <td className="px-6 py-4 text-sm">{t.user?.full_name || 'N/A'}</td>
                                            <td className="px-6 py-4 text-sm capitalize">{t.payment_method}</td>
                                            <td className="px-6 py-4 text-sm font-bold text-right">KES {t.final_amount.toFixed(2)}</td>
                                            <td className="px-6 py-4 text-sm">
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold
                                                    ${t.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                        t.status === 'voided' ? 'bg-red-100 text-red-800' :
                                                            'bg-orange-100 text-orange-800'}`}>
                                                    {t.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                ) : summary ? (
                    <div className="p-8">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-blue-50 p-6 rounded-lg border border-blue-100">
                                <h3 className="text-lg font-medium text-blue-900 mb-2">Total Sales</h3>
                                <p className="text-3xl font-bold text-blue-700">KES {summary.total_sales.toFixed(2)}</p>
                            </div>
                            <div className="bg-green-50 p-6 rounded-lg border border-green-100">
                                <h3 className="text-lg font-medium text-green-900 mb-2">Total Cash</h3>
                                <p className="text-3xl font-bold text-green-700">KES {summary.total_cash.toFixed(2)}</p>
                            </div>
                            <div className="bg-purple-50 p-6 rounded-lg border border-purple-100">
                                <h3 className="text-lg font-medium text-purple-900 mb-2">Total M-Pesa</h3>
                                <p className="text-3xl font-bold text-purple-700">KES {summary.total_mpesa.toFixed(2)}</p>
                            </div>
                            {/* Stats */}
                            <div className="md:col-span-3 grid grid-cols-2 gap-6 mt-4">
                                <div className="p-4 bg-gray-50 rounded">
                                    <p className="text-gray-500">Transaction Count</p>
                                    <p className="text-xl font-bold">{summary.transaction_count}</p>
                                </div>
                                <div className="p-4 bg-gray-50 rounded">
                                    <p className="text-gray-500">Average Value</p>
                                    <p className="text-xl font-bold">KES {summary.average_transaction.toFixed(2)}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="p-8 text-center text-gray-500">
                        Select a date range and click "Generate Report" to view summary.
                    </div>
                )}
            </div>
        </div>
    );
};

export default Reports;
