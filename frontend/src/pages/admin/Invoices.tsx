import React, { useState, useEffect } from 'react';
import { invoicesApi, Invoice, InvoicePaymentCreate } from '../../api/invoices';
import { customersApi, Customer } from '../../api/customers';

interface PaymentModalProps {
    invoice: Invoice;
    onClose: () => void;
    onSave: () => void;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ invoice, onClose, onSave }) => {
    const [formData, setFormData] = useState<InvoicePaymentCreate>({
        amount: invoice.balance,
        payment_method: 'cash',
        reference: '',
        notes: '',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await invoicesApi.recordPayment(invoice.id, formData);
            onSave();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to record payment');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
                <div className="border-b px-6 py-4 flex justify-between items-center">
                    <h2 className="text-xl font-semibold">Record Payment</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                            {error}
                        </div>
                    )}

                    <div className="bg-gray-50 p-4 rounded-md">
                        <div className="text-sm text-gray-600">Invoice: {invoice.invoice_number}</div>
                        <div className="text-lg font-semibold mt-1">
                            Outstanding: KES {invoice.balance.toLocaleString()}
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Amount (KES) *
                        </label>
                        <input
                            type="number"
                            required
                            min="0.01"
                            max={invoice.balance}
                            step="0.01"
                            value={formData.amount}
                            onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Payment Method *
                        </label>
                        <select
                            required
                            value={formData.payment_method}
                            onChange={(e) => setFormData({ ...formData, payment_method: e.target.value as any })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="cash">Cash</option>
                            <option value="mpesa">M-Pesa</option>
                            <option value="bank_transfer">Bank Transfer</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Reference
                        </label>
                        <input
                            type="text"
                            value={formData.reference || ''}
                            onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="M-Pesa code, bank ref, etc."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Notes
                        </label>
                        <textarea
                            value={formData.notes || ''}
                            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                            rows={2}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                        >
                            {loading ? 'Recording...' : 'Record Payment'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export const Invoices: React.FC = () => {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [customerFilter, setCustomerFilter] = useState<string>('');
    const [overdueOnly, setOverdueOnly] = useState(false);
    const [showPaymentModal, setShowPaymentModal] = useState(false);
    const [selectedInvoice, setSelectedInvoice] = useState<Invoice | undefined>();
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);

    const loadInvoices = async () => {
        setLoading(true);
        try {
            const response = await invoicesApi.list({
                page,
                page_size: 50,
                status_filter: statusFilter || undefined,
                customer_id: customerFilter || undefined,
                overdue_only: overdueOnly,
            });
            setInvoices(response.items);
            setTotal(response.total);
        } catch (error) {
            console.error('Failed to load invoices:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadCustomers = async () => {
        try {
            const response = await customersApi.list({ page_size: 100 });
            setCustomers(response.items);
        } catch (error) {
            console.error('Failed to load customers:', error);
        }
    };

    useEffect(() => {
        loadCustomers();
    }, []);

    useEffect(() => {
        loadInvoices();
    }, [page, statusFilter, customerFilter, overdueOnly]);

    const handleRecordPayment = (invoice: Invoice) => {
        setSelectedInvoice(invoice);
        setShowPaymentModal(true);
    };

    const handleIssue = async (invoice: Invoice) => {
        if (!confirm(`Issue invoice ${invoice.invoice_number}?`)) return;

        try {
            await invoicesApi.issue(invoice.id);
            loadInvoices();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to issue invoice');
        }
    };

    const handleCancel = async (invoice: Invoice) => {
        const reason = prompt('Reason for cancellation:');
        if (!reason) return;

        try {
            await invoicesApi.cancel(invoice.id, reason);
            loadInvoices();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to cancel invoice');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'draft': return 'bg-gray-100 text-gray-800';
            case 'issued': return 'bg-blue-100 text-blue-800';
            case 'part_paid': return 'bg-yellow-100 text-yellow-800';
            case 'paid': return 'bg-green-100 text-green-800';
            case 'overdue': return 'bg-red-100 text-red-800';
            case 'cancelled': return 'bg-gray-100 text-gray-600';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="p-6">
            <div className="mb-6 flex justify-between items-center">
                <h1 className="text-2xl font-bold">Invoices</h1>
            </div>

            {/* Filters */}
            <div className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Statuses</option>
                    <option value="draft">Draft</option>
                    <option value="issued">Issued</option>
                    <option value="part_paid">Part Paid</option>
                    <option value="paid">Paid</option>
                    <option value="overdue">Overdue</option>
                    <option value="cancelled">Cancelled</option>
                </select>

                <select
                    value={customerFilter}
                    onChange={(e) => setCustomerFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Customers</option>
                    {customers.map((customer) => (
                        <option key={customer.id} value={customer.id}>
                            {customer.name}
                        </option>
                    ))}
                </select>

                <label className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-md">
                    <input
                        type="checkbox"
                        checked={overdueOnly}
                        onChange={(e) => setOverdueOnly(e.target.checked)}
                        className="rounded"
                    />
                    <span>Overdue Only</span>
                </label>
            </div>

            {/* Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice #</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Issue Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Paid</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Balance</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr>
                                <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                                    Loading...
                                </td>
                            </tr>
                        ) : invoices.length === 0 ? (
                            <tr>
                                <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                                    No invoices found
                                </td>
                            </tr>
                        ) : (
                            invoices.map((invoice) => (
                                <tr key={invoice.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {invoice.invoice_number}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {customers.find(c => c.id === invoice.customer_id)?.name || 'Unknown'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {invoice.issue_date || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {invoice.due_date || '-'}
                                        {invoice.is_overdue && (
                                            <span className="ml-2 text-red-600 text-xs">
                                                ({invoice.days_overdue}d overdue)
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        KES {invoice.total_amount.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        KES {invoice.paid_amount.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <span className={invoice.balance > 0 ? 'text-red-600' : 'text-green-600'}>
                                            KES {invoice.balance.toLocaleString()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(invoice.status)}`}>
                                            {invoice.status.replace('_', ' ').toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                                        {invoice.status === 'draft' && (
                                            <button
                                                onClick={() => handleIssue(invoice)}
                                                className="text-blue-600 hover:text-blue-800"
                                            >
                                                Issue
                                            </button>
                                        )}
                                        {(invoice.status === 'issued' || invoice.status === 'part_paid') && (
                                            <button
                                                onClick={() => handleRecordPayment(invoice)}
                                                className="text-green-600 hover:text-green-800"
                                            >
                                                Pay
                                            </button>
                                        )}
                                        {invoice.status !== 'cancelled' && invoice.status !== 'paid' && (
                                            <button
                                                onClick={() => handleCancel(invoice)}
                                                className="text-red-600 hover:text-red-800"
                                            >
                                                Cancel
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-700">
                    Showing {invoices.length} of {total} invoices
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50"
                    >
                        Previous
                    </button>
                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={invoices.length < 50}
                        className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            </div>

            {showPaymentModal && selectedInvoice && (
                <PaymentModal
                    invoice={selectedInvoice}
                    onClose={() => setShowPaymentModal(false)}
                    onSave={loadInvoices}
                />
            )}
        </div>
    );
};
