import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { servicesApi } from '../../api/services';
import { transactionsApi } from '../../api/transactions';
import { Service, TransactionItem } from '../../types';
import { ArrowLeft, Plus, Trash2, ShoppingCart } from 'lucide-react';

const NewSale: React.FC = () => {
    const navigate = useNavigate();
    const [services, setServices] = useState<Service[]>([]);
    const [items, setItems] = useState<TransactionItem[]>([]);
    const [paymentMethod, setPaymentMethod] = useState<'cash' | 'mpesa'>('cash');
    const [mpesaCode, setMpesaCode] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        loadServices();
    }, []);

    const loadServices = async () => {
        try {
            const data = await servicesApi.list();
            setServices(data);
        } catch (error) {
            console.error('Error loading services:', error);
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

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (items.length === 0) {
            alert('Please add at least one item');
            return;
        }

        setIsLoading(true);
        try {
            await transactionsApi.create({
                items,
                payment_method: paymentMethod,
                mpesa_code: paymentMethod === 'mpesa' ? mpesaCode : undefined,
            });
            alert('Transaction completed successfully!');
            navigate('/pos');
        } catch (error: any) {
            console.error('Error creating transaction:', error);
            alert(error.response?.data?.detail || 'Failed to create transaction');
        } finally {
            setIsLoading(false);
        }
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
                                        <div className="flex gap-4">
                                            <label className="flex items-center">
                                                <input
                                                    type="radio"
                                                    value="cash"
                                                    checked={paymentMethod === 'cash'}
                                                    onChange={(e) => setPaymentMethod(e.target.value as 'cash')}
                                                    className="mr-2"
                                                />
                                                Cash
                                            </label>
                                            <label className="flex items-center">
                                                <input
                                                    type="radio"
                                                    value="mpesa"
                                                    checked={paymentMethod === 'mpesa'}
                                                    onChange={(e) => setPaymentMethod(e.target.value as 'mpesa')}
                                                    className="mr-2"
                                                />
                                                M-Pesa
                                            </label>
                                        </div>
                                    </div>

                                    {paymentMethod === 'mpesa' && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                                M-Pesa Transaction Code
                                            </label>
                                            <input
                                                type="text"
                                                value={mpesaCode}
                                                onChange={(e) => setMpesaCode(e.target.value)}
                                                className="input"
                                                placeholder="Enter M-Pesa code"
                                                required
                                            />
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={isLoading}
                                        className="w-full btn btn-primary py-3 text-lg disabled:opacity-50"
                                    >
                                        {isLoading ? 'Processing...' : 'Complete Sale'}
                                    </button>
                                </form>
                            </>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default NewSale;
