import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { servicesApi } from '../../api/services';
import { transactionsApi } from '../../api/transactions';
import { customersApi, Customer } from '../../api/customers';
import { Service, TransactionItem } from '../../types';
import { ArrowLeft, Plus, Trash2, ShoppingCart, Smartphone, User } from 'lucide-react';
import MpesaPaymentModal from '../../components/MpesaPaymentModal';

const NewSale: React.FC = () => {
    const navigate = useNavigate();
    const [services, setServices] = useState<Service[]>([]);
    const [customers, setCustomers] = useState<Customer[]>([]);
    const [items, setItems] = useState<TransactionItem[]>([]);
    const [paymentMethod, setPaymentMethod] = useState<'cash' | 'mpesa' | 'account'>('cash');
    const [mpesaCode, setMpesaCode] = useState('');
    const [selectedCustomerId, setSelectedCustomerId] = useState<string>('');
    const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showMpesaModal, setShowMpesaModal] = useState(false);
    const [pendingTransactionId, setPendingTransactionId] = useState<string | null>(null);

    useEffect(() => {
        loadServices();
        loadCustomers();
    }, []);

    const loadServices = async () => {
        try {
            const data = await servicesApi.list();
            setServices(data);
        } catch (error) {
            console.error('Error loading services:', error);
        }
    };

    const loadCustomers = async () => {
        try {
            const response = await customersApi.list({ page_size: 100, active_only: true });
            setCustomers(response.items);
        } catch (error) {
            console.error('Error loading customers:', error);
        }
    };

    const addItem = (service: Service) => {
        const newItem: TransactionItem = {
            service_id: service.id,
            description: service.name,
            quantity: 1,
            unit_price: parseFloat(service.base_price.toString()),
            total_price: parseFloat(service.base_price.toString()),
        };
        setItems([...items, newItem]);
    };

    const updateQuantity = (index: number, quantity: number) => {
        const newItems = [...items];
        newItems[index].quantity = quantity;
        newItems[index].total_price = quantity * newItems[index].unit_price;
        setItems(newItems);
    };

    const removeItem = (index: number) => {
        setItems(items.filter((_, i) => i !== index));
    };

    const total = items.reduce((sum, item) => sum + (item.total_price || 0), 0);

    // Update selected customer when customer ID changes
    useEffect(() => {
        if (selectedCustomerId) {
            const customer = customers.find(c => c.id === selectedCustomerId);
            setSelectedCustomer(customer || null);
        } else {
            setSelectedCustomer(null);
        }
    }, [selectedCustomerId, customers]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (items.length === 0) {
            alert('Please add at least one item');
            return;
        }

        // Validate ACCOUNT payment
        if (paymentMethod === 'account') {
            if (!selectedCustomerId) {
                alert('Please select a customer for account payment');
                return;
            }
            if (selectedCustomer && selectedCustomer.available_credit < total) {
                alert(`Insufficient credit. Available: KES ${selectedCustomer.available_credit.toLocaleString()}`);
                return;
            }
        }

        setIsLoading(true);
        try {
            const transaction = await transactionsApi.create({
                items,
                payment_method: paymentMethod,
                mpesa_code: paymentMethod === 'mpesa' ? mpesaCode : undefined,
                customer_id: paymentMethod === 'account' ? selectedCustomerId : undefined,
            });

            // If M-Pesa and no code provided, show STK Push modal
            if (paymentMethod === 'mpesa' && !mpesaCode) {
                setPendingTransactionId(transaction.id);
                setShowMpesaModal(true);
            } else {
                alert('Transaction completed successfully!');
                navigate('/pos');
            }
        } catch (error: any) {
            console.error('Error creating transaction:', error);
            alert(error.response?.data?.detail || 'Failed to create transaction');
        } finally {
            setIsLoading(false);
        }
    };

    const handleMpesaSuccess = (receiptNumber: string) => {
        alert(`Payment confirmed! Receipt: ${receiptNumber}`);
        navigate('/pos');
    };

    const handleMpesaFailure = (reason: string) => {
        alert(`Payment failed: ${reason}`);
        setShowMpesaModal(false);
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center gap-4">
                        <Link to="/pos" className="btn btn-secondary">
                            <ArrowLeft className="w-4 h-4" />
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-900">New Sale</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Services List */}
                    <div className="card">
                        <h2 className="text-xl font-semibold mb-4">Services</h2>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                            {services.map((service) => (
                                <button
                                    key={service.id}
                                    onClick={() => addItem(service)}
                                    className="w-full text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <p className="font-medium">{service.name}</p>
                                            <p className="text-sm text-gray-600">{service.pricing_mode.replace('_', ' ')}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-semibold">KES {parseFloat(service.base_price.toString()).toFixed(2)}</p>
                                            <Plus className="w-4 h-4 text-primary-600 ml-auto" />
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Cart */}
                    <div className="card">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <ShoppingCart className="w-6 h-6" />
                            Cart ({items.length} items)
                        </h2>

                        {items.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">No items added yet</p>
                        ) : (
                            <>
                                <div className="space-y-2 mb-6 max-h-64 overflow-y-auto">
                                    {items.map((item, index) => (
                                        <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                                            <div className="flex-1">
                                                <p className="font-medium">{item.description}</p>
                                                <p className="text-sm text-gray-600">
                                                    KES {item.unit_price.toFixed(2)} each
                                                </p>
                                            </div>
                                            <input
                                                type="number"
                                                min="1"
                                                value={item.quantity}
                                                onChange={(e) => updateQuantity(index, parseFloat(e.target.value))}
                                                className="w-20 input text-center"
                                            />
                                            <p className="font-semibold w-24 text-right">
                                                KES {(item.total_price || 0).toFixed(2)}
                                            </p>
                                            <button
                                                onClick={() => removeItem(index)}
                                                className="text-red-600 hover:text-red-700"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                <div className="border-t pt-4 mb-6">
                                    <div className="flex justify-between text-xl font-bold">
                                        <span>Total:</span>
                                        <span>KES {total.toFixed(2)}</span>
                                    </div>
                                </div>

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Payment Method
                                        </label>
                                        <div className="grid grid-cols-3 gap-2">
                                            <button
                                                type="button"
                                                onClick={() => setPaymentMethod('cash')}
                                                className={`p-3 rounded-lg border-2 transition-colors ${paymentMethod === 'cash'
                                                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                        : 'border-gray-300 hover:border-gray-400'
                                                    }`}
                                            >
                                                <div className="text-center">
                                                    <div className="text-2xl mb-1">💵</div>
                                                    <div className="text-sm font-medium">Cash</div>
                                                </div>
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setPaymentMethod('mpesa')}
                                                className={`p-3 rounded-lg border-2 transition-colors ${paymentMethod === 'mpesa'
                                                        ? 'border-green-500 bg-green-50 text-green-700'
                                                        : 'border-gray-300 hover:border-gray-400'
                                                    }`}
                                            >
                                                <div className="text-center">
                                                    <Smartphone className="w-6 h-6 mx-auto mb-1" />
                                                    <div className="text-sm font-medium">M-Pesa</div>
                                                </div>
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setPaymentMethod('account')}
                                                className={`p-3 rounded-lg border-2 transition-colors ${paymentMethod === 'account'
                                                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                                                        : 'border-gray-300 hover:border-gray-400'
                                                    }`}
                                            >
                                                <div className="text-center">
                                                    <User className="w-6 h-6 mx-auto mb-1" />
                                                    <div className="text-sm font-medium">Account</div>
                                                </div>
                                            </button>
                                        </div>
                                    </div>

                                    {paymentMethod === 'mpesa' && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                M-Pesa Code (Optional)
                                            </label>
                                            <input
                                                type="text"
                                                value={mpesaCode}
                                                onChange={(e) => setMpesaCode(e.target.value)}
                                                placeholder="Enter M-Pesa code or leave blank for STK Push"
                                                className="input w-full"
                                            />
                                            <p className="text-xs text-gray-500 mt-1">
                                                Leave blank to send STK Push to customer
                                            </p>
                                        </div>
                                    )}

                                    {paymentMethod === 'account' && (
                                        <div className="space-y-3">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Select Customer *
                                                </label>
                                                <select
                                                    value={selectedCustomerId}
                                                    onChange={(e) => setSelectedCustomerId(e.target.value)}
                                                    className="input w-full"
                                                    required
                                                >
                                                    <option value="">-- Choose Customer --</option>
                                                    {customers.map((customer) => (
                                                        <option key={customer.id} value={customer.id}>
                                                            {customer.name} ({customer.customer_number})
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>

                                            {selectedCustomer && (
                                                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                                        <div>
                                                            <span className="text-gray-600">Credit Limit:</span>
                                                            <div className="font-semibold">
                                                                KES {selectedCustomer.credit_limit.toLocaleString()}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-600">Current Balance:</span>
                                                            <div className="font-semibold">
                                                                KES {selectedCustomer.current_balance.toLocaleString()}
                                                            </div>
                                                        </div>
                                                        <div className="col-span-2">
                                                            <span className="text-gray-600">Available Credit:</span>
                                                            <div className={`font-bold text-lg ${selectedCustomer.available_credit >= total
                                                                    ? 'text-green-600'
                                                                    : 'text-red-600'
                                                                }`}>
                                                                KES {selectedCustomer.available_credit.toLocaleString()}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {selectedCustomer.available_credit < total && (
                                                        <div className="mt-2 text-xs text-red-600 font-medium">
                                                            ⚠️ Insufficient credit for this transaction
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    <button
                                        type="submit"
                                        disabled={isLoading}
                                        className="w-full btn btn-primary py-3 text-lg disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {paymentMethod === 'mpesa' && !mpesaCode && (
                                            <Smartphone className="w-5 h-5" />
                                        )}
                                        {isLoading ? 'Processing...' : paymentMethod === 'mpesa' && !mpesaCode ? 'Complete Sale & Send M-Pesa Request' : 'Complete Sale'}
                                    </button>
                                </form>
                            </>
                        )}
                    </div>
                </div>
            </main>

            {/* M-Pesa Payment Modal */}
            {showMpesaModal && pendingTransactionId && (
                <MpesaPaymentModal
                    isOpen={showMpesaModal}
                    onClose={() => setShowMpesaModal(false)}
                    transactionId={pendingTransactionId}
                    amount={total}
                    onSuccess={handleMpesaSuccess}
                    onFailure={handleMpesaFailure}
                />
            )}
        </div>
    );
};

export default NewSale;
