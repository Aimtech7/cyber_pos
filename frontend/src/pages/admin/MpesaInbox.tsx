import React, { useState, useEffect } from 'react';
import { Search, CheckCircle, XCircle, Link as LinkIcon, Loader2 } from 'lucide-react';
import { getMpesaInbox, getPotentialMatches, matchPayment, MpesaPayment } from '../../api/mpesa';
import { format } from 'date-fns';

const MpesaInbox: React.FC = () => {
    const [payments, setPayments] = useState<MpesaPayment[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterMatched, setFilterMatched] = useState<'all' | 'matched' | 'unmatched'>('all');
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [unmatchedCount, setUnmatchedCount] = useState(0);
    const [unmatchedTotal, setUnmatchedTotal] = useState(0);

    // Match dialog state
    const [matchDialogOpen, setMatchDialogOpen] = useState(false);
    const [selectedPayment, setSelectedPayment] = useState<MpesaPayment | null>(null);
    const [potentialMatches, setPotentialMatches] = useState<any[]>([]);
    const [selectedTransactionId, setSelectedTransactionId] = useState('');
    const [matchNotes, setMatchNotes] = useState('');
    const [isMatching, setIsMatching] = useState(false);

    useEffect(() => {
        loadPayments();
    }, [page, filterMatched]);

    const loadPayments = async () => {
        setLoading(true);
        try {
            const params: any = { page, page_size: 20 };

            if (filterMatched !== 'all') {
                params.is_matched = filterMatched === 'matched';
            }

            const response = await getMpesaInbox(params);
            setPayments(response.items);
            setTotal(response.total);
            setUnmatchedCount(response.unmatched_count);
            setUnmatchedTotal(response.unmatched_total);
        } catch (error) {
            console.error('Error loading M-Pesa inbox:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenMatchDialog = async (payment: MpesaPayment) => {
        setSelectedPayment(payment);
        setMatchDialogOpen(true);
        setSelectedTransactionId('');
        setMatchNotes('');

        // Load potential matches
        try {
            const response = await getPotentialMatches(payment.id);
            setPotentialMatches(response.potential_matches || []);
        } catch (error) {
            console.error('Error loading potential matches:', error);
            setPotentialMatches([]);
        }
    };

    const handleMatch = async () => {
        if (!selectedPayment || !selectedTransactionId) return;

        setIsMatching(true);
        try {
            await matchPayment({
                mpesa_payment_id: selectedPayment.id,
                transaction_id: selectedTransactionId,
                notes: matchNotes || undefined,
            });

            // Reload payments
            await loadPayments();
            setMatchDialogOpen(false);
            setSelectedPayment(null);
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to match payment');
        } finally {
            setIsMatching(false);
        }
    };

    const filteredPayments = payments.filter(payment => {
        if (!searchTerm) return true;
        const search = searchTerm.toLowerCase();
        return (
            payment.mpesa_receipt_number.toLowerCase().includes(search) ||
            payment.phone_number.includes(search) ||
            payment.amount.toString().includes(search)
        );
    });

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">M-Pesa Inbox</h1>
                <p className="text-gray-600">Manage M-Pesa payments and match to transactions</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-600">Total Payments</div>
                    <div className="text-2xl font-bold text-gray-900">{total}</div>
                </div>
                <div className="bg-yellow-50 rounded-lg shadow p-4 border border-yellow-200">
                    <div className="text-sm text-yellow-800">Unmatched Payments</div>
                    <div className="text-2xl font-bold text-yellow-900">{unmatchedCount}</div>
                </div>
                <div className="bg-green-50 rounded-lg shadow p-4 border border-green-200">
                    <div className="text-sm text-green-800">Unmatched Amount</div>
                    <div className="text-2xl font-bold text-green-900">
                        KES {unmatchedTotal.toLocaleString()}
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow mb-6 p-4">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                            <input
                                type="text"
                                placeholder="Search by receipt, phone, or amount..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            />
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setFilterMatched('all')}
                            className={`px-4 py-2 rounded-lg ${filterMatched === 'all'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            All
                        </button>
                        <button
                            onClick={() => setFilterMatched('matched')}
                            className={`px-4 py-2 rounded-lg ${filterMatched === 'matched'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Matched
                        </button>
                        <button
                            onClick={() => setFilterMatched('unmatched')}
                            className={`px-4 py-2 rounded-lg ${filterMatched === 'unmatched'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Unmatched
                        </button>
                    </div>
                </div>
            </div>

            {/* Payments Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 text-green-600 animate-spin" />
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b">
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
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {filteredPayments.map((payment) => (
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
                                            {format(new Date(payment.transaction_date), 'MMM dd, yyyy HH:mm')}
                                        </td>
                                        <td className="px-6 py-4">
                                            {payment.is_matched ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                                                    <CheckCircle className="w-3 h-3" />
                                                    Matched
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                                                    <XCircle className="w-3 h-3" />
                                                    Unmatched
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            {!payment.is_matched && (
                                                <button
                                                    onClick={() => handleOpenMatchDialog(payment)}
                                                    className="inline-flex items-center gap-1 text-green-600 hover:text-green-700 text-sm font-medium"
                                                >
                                                    <LinkIcon className="w-4 h-4" />
                                                    Match
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination */}
                {total > 20 && (
                    <div className="px-6 py-4 border-t flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total}
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(page - 1)}
                                disabled={page === 1}
                                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPage(page + 1)}
                                disabled={page * 20 >= total}
                                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Match Dialog */}
            {matchDialogOpen && selectedPayment && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                        <div className="p-6 border-b">
                            <h2 className="text-xl font-semibold">Match Payment to Transaction</h2>
                            <p className="text-sm text-gray-600 mt-1">
                                Receipt: {selectedPayment.mpesa_receipt_number} | Amount: KES {selectedPayment.amount}
                            </p>
                        </div>

                        <div className="p-6 space-y-4">
                            {potentialMatches.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                                        Potential Matches ({potentialMatches.length})
                                    </h3>
                                    <div className="space-y-2">
                                        {potentialMatches.map((match: any) => (
                                            <label
                                                key={match.id}
                                                className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                                            >
                                                <input
                                                    type="radio"
                                                    name="transaction"
                                                    value={match.id}
                                                    checked={selectedTransactionId === match.id}
                                                    onChange={(e) => setSelectedTransactionId(e.target.value)}
                                                    className="text-green-600 focus:ring-green-500"
                                                />
                                                <div className="flex-1">
                                                    <div className="font-medium">Transaction #{match.transaction_number}</div>
                                                    <div className="text-sm text-gray-600">
                                                        KES {match.final_amount} | {format(new Date(match.created_at), 'MMM dd, HH:mm')}
                                                    </div>
                                                </div>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Or enter Transaction ID manually
                                </label>
                                <input
                                    type="text"
                                    value={selectedTransactionId}
                                    onChange={(e) => setSelectedTransactionId(e.target.value)}
                                    placeholder="Transaction UUID"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Notes (Optional)
                                </label>
                                <textarea
                                    value={matchNotes}
                                    onChange={(e) => setMatchNotes(e.target.value)}
                                    placeholder="Add any notes about this match..."
                                    rows={3}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                />
                            </div>
                        </div>

                        <div className="p-6 border-t flex gap-3">
                            <button
                                onClick={() => setMatchDialogOpen(false)}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                disabled={isMatching}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleMatch}
                                disabled={!selectedTransactionId || isMatching}
                                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {isMatching ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Matching...
                                    </>
                                ) : (
                                    'Confirm Match'
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MpesaInbox;
