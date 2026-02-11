import React, { useEffect, useState } from 'react';
import { transactionsApi } from '../../api/transactions';
import { Transaction, TransactionStatus } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { Search, Printer, RotateCcw, Ban, Eye, FileText } from 'lucide-react';

const Transactions: React.FC = () => {
    const { user } = useAuth();
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    // Receipt Modal
    const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
    const [showReceipt, setShowReceipt] = useState(false);

    // Action Modal (Void/Refund)
    const [actionType, setActionType] = useState<'void' | 'refund' | null>(null);
    const [actionReason, setActionReason] = useState('');
    const [showActionModal, setShowActionModal] = useState(false);

    useEffect(() => {
        loadTransactions();
    }, []);

    const loadTransactions = async () => {
        setLoading(true);
        try {
            const data = await transactionsApi.list();
            setTransactions(data);
        } catch (error) {
            console.error('Error loading transactions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePrintReceipt = (transaction: Transaction) => {
        setSelectedTransaction(transaction);
        setShowReceipt(true);
    };

    const handleAction = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedTransaction || !actionType) return;

        try {
            if (actionType === 'void') {
                await transactionsApi.void(selectedTransaction.id, actionReason);
            } else {
                await transactionsApi.refund(selectedTransaction.id, actionReason);
            }
            setShowActionModal(false);
            setActionType(null);
            setActionReason('');
            setSelectedTransaction(null);
            loadTransactions();
        } catch (error) {
            console.error(`Error ${actionType}ing transaction:`, error);
            alert(`Failed to ${actionType} transaction`);
        }
    };

    const openActionModal = (transaction: Transaction, type: 'void' | 'refund') => {
        setSelectedTransaction(transaction);
        setActionType(type);
        setActionReason('');
        setShowActionModal(true);
    };

    const filteredTransactions = transactions.filter(t =>
        t.transaction_number.toString().includes(searchTerm) ||
        t.transaction_items.some(i => i.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // Can user void/refund?
    const canManageTransactions = user?.role === 'ADMIN' || user?.role === 'MANAGER';

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Transaction History</h1>

            <div className="flex gap-4 mb-6">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Search by ID or Item..."
                        className="input pl-10 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan={7} className="p-4 text-center">Loading...</td></tr>
                        ) : filteredTransactions.length === 0 ? (
                            <tr><td colSpan={7} className="p-4 text-center">No transactions found</td></tr>
                        ) : (
                            filteredTransactions.map((t) => (
                                <tr key={t.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap font-medium">#{t.transaction_number}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(t.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {t.transaction_items.length} items
                                        <div className="text-xs text-gray-400 truncate max-w-xs">
                                            {t.transaction_items.map(i => i.description).join(', ')}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap font-bold">
                                        KES {parseFloat(t.final_amount.toString()).toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm capitalize">
                                        {t.payment_method}
                                        {t.mpesa_code && <span className="block text-xs text-gray-400">{t.mpesa_code}</span>}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold
                                            ${t.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                t.status === 'voided' ? 'bg-red-100 text-red-800' :
                                                    'bg-orange-100 text-orange-800'}`}>
                                            {t.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => handlePrintReceipt(t)}
                                            className="text-gray-600 hover:text-gray-900 mr-3"
                                            title="View Receipt"
                                        >
                                            <Printer size={18} />
                                        </button>

                                        {canManageTransactions && t.status === 'completed' && (
                                            <>
                                                <button
                                                    onClick={() => openActionModal(t, 'void')}
                                                    className="text-red-600 hover:text-red-900 mr-3"
                                                    title="Void Transaction"
                                                >
                                                    <Ban size={18} />
                                                </button>
                                                <button
                                                    onClick={() => openActionModal(t, 'refund')}
                                                    className="text-orange-600 hover:text-orange-900"
                                                    title="Refund Transaction"
                                                >
                                                    <RotateCcw size={18} />
                                                </button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Receipt Modal */}
            {showReceipt && selectedTransaction && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-sm">
                        <div id="receipt-content" className="font-mono text-sm mb-6 bg-gray-50 p-4 rounded border border-gray-200">
                            <div className="text-center mb-4">
                                <h2 className="font-bold text-lg">CyberCafe POS Pro</h2>
                                <p>Tel: 0700 000 000</p>
                                <p>{new Date(selectedTransaction.created_at).toLocaleString()}</p>
                                <p>Rcpt #: {selectedTransaction.transaction_number}</p>
                            </div>
                            <div className="border-b border-dashed border-gray-400 my-2"></div>
                            <div className="space-y-2">
                                {selectedTransaction.transaction_items.map((item, idx) => (
                                    <div key={idx} className="flex justify-between">
                                        <span className="truncate w-32">{item.description}</span>
                                        <span>{item.quantity} x {item.unit_price}</span>
                                        <span>{item.total_price}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="border-b border-dashed border-gray-400 my-2"></div>
                            <div className="flex justify-between font-bold">
                                <span>TOTAL</span>
                                <span>KES {parseFloat(selectedTransaction.final_amount.toString()).toFixed(2)}</span>
                            </div>
                            <div className="mt-2 text-xs text-center text-gray-500">
                                Payment: {selectedTransaction.payment_method.toUpperCase()}
                                {selectedTransaction.mpesa_code && <br /> + `M-Pesa: ${selectedTransaction.mpesa_code}`}
                            </div>
                        </div>
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setShowReceipt(false)} className="btn btn-secondary">Close</button>
                            <button
                                onClick={() => {
                                    // Print logic (basic window print for now, ideally print specific div)
                                    // A simple way is to open a new window and print it
                                    const printContent = document.getElementById('receipt-content')?.innerHTML;
                                    const win = window.open('', '', 'height=500,width=400');
                                    if (win && printContent) {
                                        win.document.write('<html><head><title>Receipt</title></head><body>');
                                        win.document.write(printContent);
                                        win.document.write('</body></html>');
                                        win.document.close();
                                        win.print();
                                    }
                                }}
                                className="btn btn-primary flex items-center gap-2"
                            >
                                <Printer size={16} /> Print
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Action Modal */}
            {showActionModal && selectedTransaction && actionType && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4 capitalize">{actionType} Transaction #{selectedTransaction.transaction_number}</h2>
                        <div className="bg-red-50 text-red-700 p-3 rounded mb-4 text-sm">
                            Warning: This will reverse stock and update shift totals.
                        </div>
                        <form onSubmit={handleAction}>
                            <div className="mb-4">
                                <label className="label">Reason for {actionType}</label>
                                <textarea
                                    className="input w-full"
                                    value={actionReason}
                                    onChange={e => setActionReason(e.target.value)}
                                    required
                                    rows={3}
                                    placeholder="e.g. Mistake entry, Customer complaint..."
                                />
                            </div>
                            <div className="flex justify-end gap-2">
                                <button type="button" onClick={() => setShowActionModal(false)} className="btn btn-secondary">Cancel</button>
                                <button type="submit" className="btn btn-danger capitalize">Confirm {actionType}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Transactions;
