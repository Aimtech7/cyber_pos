import React, { useState, useEffect } from 'react';
import { X, Smartphone, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { initiatePayment, checkPaymentStatus, PaymentIntentResponse } from '../api/mpesa';

interface MpesaPaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    transactionId: string;
    amount: number;
    onSuccess: (receiptNumber: string) => void;
    onFailure: (reason: string) => void;
}

const MpesaPaymentModal: React.FC<MpesaPaymentModalProps> = ({
    isOpen,
    onClose,
    transactionId,
    amount,
    onSuccess,
    onFailure,
}) => {
    const [phoneNumber, setPhoneNumber] = useState('254');
    const [isProcessing, setIsProcessing] = useState(false);
    const [paymentIntent, setPaymentIntent] = useState<PaymentIntentResponse | null>(null);
    const [status, setStatus] = useState<'idle' | 'pending' | 'confirmed' | 'failed' | 'expired'>('idle');
    const [message, setMessage] = useState('');
    const [timeRemaining, setTimeRemaining] = useState(90);

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setPhoneNumber('254');
            setIsProcessing(false);
            setPaymentIntent(null);
            setStatus('idle');
            setMessage('');
            setTimeRemaining(90);
        }
    }, [isOpen]);

    // Countdown timer
    useEffect(() => {
        if (status === 'pending' && timeRemaining > 0) {
            const timer = setTimeout(() => {
                setTimeRemaining(timeRemaining - 1);
            }, 1000);
            return () => clearTimeout(timer);
        } else if (status === 'pending' && timeRemaining === 0) {
            setStatus('expired');
            setMessage('Payment request expired. Please try again.');
        }
    }, [status, timeRemaining]);

    // Poll payment status
    useEffect(() => {
        if (!paymentIntent || status !== 'pending') return;

        const pollInterval = setInterval(async () => {
            try {
                const updated = await checkPaymentStatus(paymentIntent.id);

                if (updated.status === 'confirmed') {
                    setStatus('confirmed');
                    setMessage('Payment confirmed successfully!');
                    clearInterval(pollInterval);
                    setTimeout(() => {
                        onSuccess(updated.mpesa_receipt_number || '');
                        onClose();
                    }, 2000);
                } else if (updated.status === 'failed') {
                    setStatus('failed');
                    setMessage(updated.failure_reason || 'Payment failed');
                    clearInterval(pollInterval);
                    setTimeout(() => {
                        onFailure(updated.failure_reason || 'Payment failed');
                    }, 3000);
                } else if (updated.status === 'expired') {
                    setStatus('expired');
                    setMessage('Payment request expired');
                    clearInterval(pollInterval);
                }
            } catch (error) {
                console.error('Error polling payment status:', error);
            }
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(pollInterval);
    }, [paymentIntent, status, onSuccess, onFailure, onClose]);

    const handleInitiatePayment = async () => {
        // Validate phone number
        if (!/^254\d{9}$/.test(phoneNumber)) {
            setMessage('Invalid phone number. Format: 254XXXXXXXXX');
            return;
        }

        setIsProcessing(true);
        setMessage('');

        try {
            const response = await initiatePayment({
                transaction_id: transactionId,
                phone_number: phoneNumber,
                amount: amount,
            });

            setPaymentIntent({
                id: response.payment_intent_id,
                transaction_id: transactionId,
                amount: amount,
                phone_number: phoneNumber,
                status: 'pending',
                mpesa_checkout_request_id: response.checkout_request_id,
                created_at: new Date().toISOString(),
                expires_at: new Date(Date.now() + 90000).toISOString(),
                is_expired: false,
                is_pending: true,
            });

            setStatus('pending');
            setMessage(response.customer_message || 'Check your phone for M-Pesa prompt');
            setTimeRemaining(90);
        } catch (error: any) {
            setStatus('failed');
            setMessage(error.response?.data?.detail || 'Failed to initiate payment');
            setIsProcessing(false);
        }
    };

    const handleCancel = () => {
        if (status === 'pending') {
            if (!confirm('Payment is pending. Are you sure you want to cancel?')) {
                return;
            }
        }
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                            <Smartphone className="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-gray-900">M-Pesa Payment</h2>
                            <p className="text-sm text-gray-500">KES {amount.toLocaleString()}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleCancel}
                        className="text-gray-400 hover:text-gray-600"
                        disabled={isProcessing}
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4">
                    {status === 'idle' && (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Phone Number
                                </label>
                                <input
                                    type="tel"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    placeholder="254712345678"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                    disabled={isProcessing}
                                />
                                <p className="mt-1 text-xs text-gray-500">
                                    Format: 254XXXXXXXXX (Safaricom, Airtel)
                                </p>
                            </div>

                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h3 className="text-sm font-medium text-blue-900 mb-2">How it works:</h3>
                                <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                                    <li>Enter your M-Pesa phone number</li>
                                    <li>Click "Send Payment Request"</li>
                                    <li>Check your phone for M-Pesa prompt</li>
                                    <li>Enter your M-Pesa PIN</li>
                                    <li>Payment confirms automatically</li>
                                </ol>
                            </div>
                        </>
                    )}

                    {status === 'pending' && (
                        <div className="text-center py-6">
                            <Loader2 className="w-16 h-16 text-green-600 animate-spin mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                Waiting for Payment
                            </h3>
                            <p className="text-gray-600 mb-4">{message}</p>
                            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                                <Clock className="w-4 h-4" />
                                <span>Expires in {timeRemaining}s</span>
                            </div>
                            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                                <p className="text-sm text-yellow-800">
                                    Check your phone for the M-Pesa prompt and enter your PIN
                                </p>
                            </div>
                        </div>
                    )}

                    {status === 'confirmed' && (
                        <div className="text-center py-6">
                            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                Payment Successful!
                            </h3>
                            <p className="text-gray-600">{message}</p>
                        </div>
                    )}

                    {(status === 'failed' || status === 'expired') && (
                        <div className="text-center py-6">
                            <XCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                {status === 'expired' ? 'Payment Expired' : 'Payment Failed'}
                            </h3>
                            <p className="text-gray-600 mb-4">{message}</p>
                            <button
                                onClick={() => {
                                    setStatus('idle');
                                    setMessage('');
                                    setIsProcessing(false);
                                }}
                                className="text-green-600 hover:text-green-700 font-medium"
                            >
                                Try Again
                            </button>
                        </div>
                    )}

                    {message && status === 'idle' && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <p className="text-sm text-red-800">{message}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                {status === 'idle' && (
                    <div className="flex gap-3 p-6 border-t">
                        <button
                            onClick={handleCancel}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                            disabled={isProcessing}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleInitiatePayment}
                            disabled={isProcessing || phoneNumber.length !== 12}
                            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Sending...
                                </>
                            ) : (
                                'Send Payment Request'
                            )}
                        </button>
                    </div>
                )}

                {status === 'pending' && (
                    <div className="p-6 border-t">
                        <button
                            onClick={handleCancel}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MpesaPaymentModal;
