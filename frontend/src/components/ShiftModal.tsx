import React, { useState } from 'react';
import { useShift } from '../context/ShiftContext';
import { X } from 'lucide-react';

interface ShiftModalProps {
    isOpen: boolean;
    onClose: () => void;
    mode: 'open' | 'close';
}

const ShiftModal: React.FC<ShiftModalProps> = ({ isOpen, onClose, mode }) => {
    const { openShift, closeShift, currentShift } = useShift();
    const [amount, setAmount] = useState('');
    const [notes, setNotes] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSubmitting(true);

        try {
            const cashAmount = parseFloat(amount);
            if (isNaN(cashAmount) || cashAmount < 0) {
                throw new Error('Please enter a valid amount');
            }

            if (mode === 'open') {
                await openShift(cashAmount);
            } else {
                await closeShift(cashAmount, notes);
            }
            onClose();
        } catch (err: any) {
            setError(err.message || 'Failed to process shift');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold">
                        {mode === 'open' ? 'Open New Shift' : 'Close Current Shift'}
                    </h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                        <X size={24} />
                    </button>
                </div>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                {mode === 'close' && currentShift && (
                    <div className="bg-gray-50 p-4 rounded mb-4 text-sm">
                        <div className="flex justify-between mb-1">
                            <span>Expected Cash:</span>
                            <span className="font-semibold">KES {currentShift.expected_cash}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Total Sales:</span>
                            <span className="font-semibold">KES {currentShift.total_sales}</span>
                        </div>
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2">
                            {mode === 'open' ? 'Opening Cash Amount' : 'Counted Cash Amount'}
                        </label>
                        <input
                            type="number"
                            step="0.01"
                            className="input w-full"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            placeholder="0.00"
                            required
                        />
                    </div>

                    {mode === 'close' && (
                        <div className="mb-4">
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Closing Notes
                            </label>
                            <textarea
                                className="input w-full"
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="Any discrepancies or notes..."
                                rows={3}
                            />
                        </div>
                    )}

                    <div className="flex justify-end gap-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="btn btn-secondary"
                            disabled={submitting}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={submitting}
                        >
                            {submitting ? 'Processing...' : (mode === 'open' ? 'Open Shift' : 'Close Shift')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ShiftModal;
