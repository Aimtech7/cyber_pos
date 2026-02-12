import React, { useState, useEffect } from 'react';
import { Calendar, Download, TrendingUp, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react';
import { getReconciliationReport, ReconciliationReport } from '../../api/mpesa';
import { format } from 'date-fns';

const MpesaReconciliation: React.FC = () => {
    const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [report, setReport] = useState<ReconciliationReport | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadReport();
    }, [selectedDate]);

    const loadReport = async () => {
        setLoading(true);
        try {
            const data = await getReconciliationReport(selectedDate);
            setReport(data);
        } catch (error) {
            console.error('Error loading reconciliation report:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!report) return;

        // Create CSV content
        const headers = ['Type', 'Receipt/ID', 'Amount', 'Phone', 'Date', 'Status'];
        const rows: string[][] = [];

        // Add unmatched payments
        report.unmatched_payments.forEach(payment => {
            rows.push([
                'Unmatched Payment',
                payment.mpesa_receipt_number,
                payment.amount.toString(),
                payment.phone_number,
                format(new Date(payment.transaction_date), 'yyyy-MM-dd HH:mm:ss'),
                'Unmatched'
            ]);
        });

        // Add failed intents
        report.failed_intents.forEach(intent => {
            rows.push([
                'Failed Intent',
                intent.id,
                intent.amount.toString(),
                intent.phone_number,
                format(new Date(intent.created_at), 'yyyy-MM-dd HH:mm:ss'),
                intent.failure_reason || 'Failed'
            ]);
        });

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        // Download
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mpesa-reconciliation-${selectedDate}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">M-Pesa Reconciliation</h1>
                    <p className="text-gray-600">Daily M-Pesa payment reconciliation report</p>
                </div>
                <button
                    onClick={handleExportCSV}
                    disabled={!report}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                    <Download className="w-4 h-4" />
                    Export CSV
                </button>
            </div>

            {/* Date Selector */}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
                <div className="flex items-center gap-4">
                    <Calendar className="w-5 h-5 text-gray-400" />
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        max={format(new Date(), 'yyyy-MM-dd')}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                    <button
                        onClick={() => setSelectedDate(format(new Date(), 'yyyy-MM-dd'))}
                        className="px-4 py-2 text-green-600 hover:text-green-700 font-medium"
                    >
                        Today
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
                </div>
            ) : report ? (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white rounded-lg shadow p-4">
                            <div className="text-sm text-gray-600 mb-1">Expected M-Pesa</div>
                            <div className="text-2xl font-bold text-gray-900">
                                KES {report.expected_mpesa_total.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                                {report.expected_mpesa_count} transactions
                            </div>
                        </div>

                        <div className="bg-green-50 rounded-lg shadow p-4 border border-green-200">
                            <div className="text-sm text-green-800 mb-1">Confirmed M-Pesa</div>
                            <div className="text-2xl font-bold text-green-900">
                                KES {report.confirmed_total.toLocaleString()}
                            </div>
                            <div className="text-xs text-green-700 mt-1">
                                {report.confirmed_count} payments
                            </div>
                        </div>

                        <div className="bg-yellow-50 rounded-lg shadow p-4 border border-yellow-200">
                            <div className="text-sm text-yellow-800 mb-1">Unmatched</div>
                            <div className="text-2xl font-bold text-yellow-900">
                                KES {report.unmatched_total.toLocaleString()}
                            </div>
                            <div className="text-xs text-yellow-700 mt-1">
                                {report.unmatched_count} payments
                            </div>
                        </div>

                        <div className={`rounded-lg shadow p-4 border ${report.variance_amount >= 0
                                ? 'bg-blue-50 border-blue-200'
                                : 'bg-red-50 border-red-200'
                            }`}>
                            <div className={`text-sm mb-1 ${report.variance_amount >= 0 ? 'text-blue-800' : 'text-red-800'
                                }`}>
                                Variance
                            </div>
                            <div className={`text-2xl font-bold flex items-center gap-2 ${report.variance_amount >= 0 ? 'text-blue-900' : 'text-red-900'
                                }`}>
                                {report.variance_amount >= 0 ? (
                                    <TrendingUp className="w-6 h-6" />
                                ) : (
                                    <TrendingDown className="w-6 h-6" />
                                )}
                                KES {Math.abs(report.variance_amount).toLocaleString()}
                            </div>
                            <div className={`text-xs mt-1 ${report.variance_amount >= 0 ? 'text-blue-700' : 'text-red-700'
                                }`}>
                                {report.variance_percentage.toFixed(2)}%
                            </div>
                        </div>
                    </div>

                    {/* Failed & Expired */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="bg-red-50 rounded-lg shadow p-4 border border-red-200">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertCircle className="w-5 h-5 text-red-600" />
                                <div className="text-sm font-medium text-red-800">Failed Payments</div>
                            </div>
                            <div className="text-2xl font-bold text-red-900">
                                {report.failed_count}
                            </div>
                            <div className="text-sm text-red-700 mt-1">
                                KES {report.failed_total.toLocaleString()}
                            </div>
                        </div>

                        <div className="bg-gray-50 rounded-lg shadow p-4 border border-gray-200">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertCircle className="w-5 h-5 text-gray-600" />
                                <div className="text-sm font-medium text-gray-800">Expired Intents</div>
                            </div>
                            <div className="text-2xl font-bold text-gray-900">
                                {report.expired_count}
                            </div>
                            <div className="text-sm text-gray-700 mt-1">
                                KES {report.expired_total.toLocaleString()}
                            </div>
                        </div>
                    </div>

                    {/* Unmatched Payments Table */}
                    {report.unmatched_payments.length > 0 && (
                        <div className="bg-white rounded-lg shadow mb-6">
                            <div className="p-4 border-b">
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Unmatched Payments ({report.unmatched_payments.length})
                                </h2>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Receipt Number
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Amount
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Phone
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Date
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        {report.unmatched_payments.map((payment) => (
                                            <tr key={payment.id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                                    {payment.mpesa_receipt_number}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-900">
                                                    KES {payment.amount.toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-600">
                                                    {payment.phone_number}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-600">
                                                    {format(new Date(payment.transaction_date), 'MMM dd, HH:mm')}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Failed Intents Table */}
                    {report.failed_intents.length > 0 && (
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-4 border-b">
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Failed Payment Intents ({report.failed_intents.length})
                                </h2>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Transaction ID
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Amount
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Phone
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Failure Reason
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                                Date
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        {report.failed_intents.map((intent) => (
                                            <tr key={intent.id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 text-sm font-mono text-gray-900">
                                                    {intent.transaction_id.substring(0, 8)}...
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-900">
                                                    KES {intent.amount.toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-600">
                                                    {intent.phone_number}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-red-600">
                                                    {intent.failure_reason || 'Unknown'}
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-600">
                                                    {format(new Date(intent.created_at), 'MMM dd, HH:mm')}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Success Message */}
                    {report.variance_amount === 0 && report.unmatched_count === 0 && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                            <h3 className="text-lg font-semibold text-green-900 mb-1">
                                Perfect Reconciliation!
                            </h3>
                            <p className="text-green-700">
                                All M-Pesa payments are matched and reconciled.
                            </p>
                        </div>
                    )}
                </>
            ) : (
                <div className="bg-gray-50 rounded-lg p-12 text-center">
                    <p className="text-gray-600">No data available for selected date</p>
                </div>
            )}
        </div>
    );
};

export default MpesaReconciliation;
