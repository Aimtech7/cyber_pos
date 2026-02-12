/**
 * Offline Queue Page
 * View and manage pending offline transactions
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, XCircle, Clock, Eye, Trash2 } from 'lucide-react';
import { offlineStorage, PendingTransaction } from '../../services/offlineStorage';
import { useOffline } from '../../context/OfflineContext';

export const OfflineQueue: React.FC = () => {
    const [transactions, setTransactions] = useState<PendingTransaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTransaction, setSelectedTransaction] = useState<PendingTransaction | null>(null);
    const { manualSync, isSyncing } = useOffline();

    useEffect(() => {
        loadTransactions();
    }, []);

    const loadTransactions = async () => {
        setLoading(true);
        try {
            const allTransactions = await offlineStorage.getAllTransactions();
            setTransactions(allTransactions);
        } catch (error) {
            console.error('Failed to load transactions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleClearQueue = async () => {
        if (!confirm('Are you sure you want to clear all transactions? This cannot be undone.')) {
            return;
        }

        try {
            await offlineStorage.clearAll();
            await loadTransactions();
        } catch (error) {
            console.error('Failed to clear queue:', error);
            alert('Failed to clear queue');
        }
    };

    const handleDeleteTransaction = async (id: string) => {
        if (!confirm('Are you sure you want to delete this transaction?')) {
            return;
        }

        try {
            await offlineStorage.removeTransaction(id);
            await loadTransactions();
        } catch (error) {
            console.error('Failed to delete transaction:', error);
            alert('Failed to delete transaction');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'PENDING': return 'bg-yellow-100 text-yellow-800';
            case 'SYNCING': return 'bg-blue-100 text-blue-800';
            case 'SYNCED': return 'bg-green-100 text-green-800';
            case 'FAILED': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'PENDING': return <Clock className="w-4 h-4" />;
            case 'SYNCING': return <RefreshCw className="w-4 h-4 animate-spin" />;
            case 'SYNCED': return <CheckCircle className="w-4 h-4" />;
            case 'FAILED': return <XCircle className="w-4 h-4" />;
            default: return null;
        }
    };

    const pendingCount = transactions.filter(t => t.status === 'PENDING' || t.status === 'FAILED').length;

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold">Offline Transaction Queue</h1>
                    <p className="text-gray-600 mt-1">
                        {pendingCount} transaction{pendingCount !== 1 ? 's' : ''} pending sync
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={loadTransactions}
                        disabled={loading}
                        className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 flex items-center gap-2"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    {pendingCount > 0 && (
                        <button
                            onClick={() => manualSync()}
                            disabled={isSyncing}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                            {isSyncing ? 'Syncing...' : 'Sync Now'}
                        </button>
                    )}
                    <button
                        onClick={handleClearQueue}
                        disabled={transactions.length === 0}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                    >
                        Clear All
                    </button>
                </div>
            </div>

            {/* Transactions List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center">Loading...</div>
                ) : transactions.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">No transactions in queue</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Receipt</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Payment</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Items</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Created</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Retries</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {transactions.map((transaction) => (
                                    <tr key={transaction.id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3">
                                            <div className="text-sm font-medium">
                                                {transaction.offline_receipt_number}
                                            </div>
                                            {transaction.synced_receipt_number && (
                                                <div className="text-xs text-gray-500">
                                                    → #{transaction.synced_receipt_number}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold uppercase flex items-center gap-1 w-fit ${getStatusColor(transaction.status)}`}>
                                                {getStatusIcon(transaction.status)}
                                                {transaction.status}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm capitalize">
                                            {transaction.transaction_data.payment_method}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {transaction.transaction_data.items.length} item{transaction.transaction_data.items.length !== 1 ? 's' : ''}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {new Date(transaction.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {transaction.retry_count}
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => setSelectedTransaction(transaction)}
                                                    className="text-blue-600 hover:text-blue-800"
                                                    title="View Details"
                                                >
                                                    <Eye className="w-4 h-4" />
                                                </button>
                                                {transaction.status !== 'SYNCED' && (
                                                    <button
                                                        onClick={() => handleDeleteTransaction(transaction.id)}
                                                        className="text-red-600 hover:text-red-800"
                                                        title="Delete"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Details Modal */}
            {selectedTransaction && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-start mb-4">
                            <h2 className="text-xl font-bold">Transaction Details</h2>
                            <button onClick={() => setSelectedTransaction(null)}>
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="font-semibold">Offline Receipt:</label>
                                <p>{selectedTransaction.offline_receipt_number}</p>
                            </div>

                            {selectedTransaction.synced_receipt_number && (
                                <div>
                                    <label className="font-semibold">Official Receipt:</label>
                                    <p>#{selectedTransaction.synced_receipt_number}</p>
                                </div>
                            )}

                            <div>
                                <label className="font-semibold">Status:</label>
                                <span className={`ml-2 px-2 py-1 rounded text-xs font-semibold uppercase ${getStatusColor(selectedTransaction.status)}`}>
                                    {selectedTransaction.status}
                                </span>
                            </div>

                            <div>
                                <label className="font-semibold">Items:</label>
                                <ul className="mt-2 space-y-2">
                                    {selectedTransaction.transaction_data.items.map((item, idx) => (
                                        <li key={idx} className="flex justify-between bg-gray-50 p-2 rounded">
                                            <span>{item.description} (x{item.quantity})</span>
                                            <span className="font-medium">
                                                KES {(item.quantity * item.unit_price).toFixed(2)}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div>
                                <label className="font-semibold">Payment Method:</label>
                                <p className="capitalize">{selectedTransaction.transaction_data.payment_method}</p>
                            </div>

                            {selectedTransaction.last_error && (
                                <div>
                                    <label className="font-semibold text-red-600">Last Error:</label>
                                    <p className="text-red-600">{selectedTransaction.last_error}</p>
                                </div>
                            )}

                            <div>
                                <label className="font-semibold">Created:</label>
                                <p>{new Date(selectedTransaction.created_at).toLocaleString()}</p>
                            </div>

                            <div>
                                <label className="font-semibold">Retry Count:</label>
                                <p>{selectedTransaction.retry_count}</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
