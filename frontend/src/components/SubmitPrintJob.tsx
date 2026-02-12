import React, { useState, useEffect } from 'react';
import { Printer, X } from 'lucide-react';
import { printJobsApi, PrintJobCreate } from '../api/printJobs';
import { computersApi, Computer } from '../api/computers';

interface SubmitPrintJobProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

const SubmitPrintJob: React.FC<SubmitPrintJobProps> = ({ isOpen, onClose, onSuccess }) => {
    const [computers, setComputers] = useState<Computer[]>([]);
    const [formData, setFormData] = useState<PrintJobCreate>({
        computer_id: '',
        requested_by: '',
        description: '',
        pages_bw: 0,
        pages_color: 0,
    });
    const [loading, setLoading] = useState(false);
    const [estimatedCost, setEstimatedCost] = useState(0);

    useEffect(() => {
        if (isOpen) {
            loadComputers();
        }
    }, [isOpen]);

    useEffect(() => {
        // Estimate cost (rough calculation, server will compute exact)
        // Assuming KES 5 per B&W page, KES 10 per color page
        const bwCost = formData.pages_bw * 5;
        const colorCost = formData.pages_color * 10;
        setEstimatedCost(bwCost + colorCost);
    }, [formData.pages_bw, formData.pages_color]);

    const loadComputers = async () => {
        try {
            const data = await computersApi.list();
            setComputers(data);
        } catch (error) {
            console.error('Error loading computers:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.computer_id) {
            alert('Please select a computer');
            return;
        }

        if (!formData.requested_by.trim()) {
            alert('Please enter customer name');
            return;
        }

        if (formData.pages_bw === 0 && formData.pages_color === 0) {
            alert('Please enter at least one page (B&W or Color)');
            return;
        }

        setLoading(true);
        try {
            const job = await printJobsApi.submit(formData);
            alert(`Print job ${job.job_number} submitted successfully!\n\nTotal: KES ${job.total_amount}`);

            // Reset form
            setFormData({
                computer_id: '',
                requested_by: '',
                description: '',
                pages_bw: 0,
                pages_color: 0,
            });

            if (onSuccess) {
                onSuccess();
            }
            onClose();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to submit print job');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <div className="flex items-center gap-3">
                        <Printer className="w-6 h-6 text-green-600" />
                        <h2 className="text-xl font-semibold text-gray-900">Submit Print Job</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {/* Computer Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Computer *
                        </label>
                        <select
                            value={formData.computer_id}
                            onChange={(e) => setFormData({ ...formData, computer_id: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            required
                        >
                            <option value="">Select computer...</option>
                            {computers.map((computer) => (
                                <option key={computer.id} value={computer.id}>
                                    {computer.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Customer Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Customer Name *
                        </label>
                        <input
                            type="text"
                            value={formData.requested_by}
                            onChange={(e) => setFormData({ ...formData, requested_by: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Enter customer name"
                            required
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Description (Optional)
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            rows={2}
                            placeholder="e.g., Assignment, CV, Photos..."
                        />
                    </div>

                    {/* Pages */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                B&W Pages
                            </label>
                            <input
                                type="number"
                                min="0"
                                value={formData.pages_bw}
                                onChange={(e) => setFormData({ ...formData, pages_bw: parseInt(e.target.value) || 0 })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Color Pages
                            </label>
                            <input
                                type="number"
                                min="0"
                                value={formData.pages_color}
                                onChange={(e) => setFormData({ ...formData, pages_color: parseInt(e.target.value) || 0 })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            />
                        </div>
                    </div>

                    {/* Estimated Cost */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-green-900">Estimated Total:</span>
                            <span className="text-xl font-bold text-green-600">
                                KES {estimatedCost.toLocaleString()}
                            </span>
                        </div>
                        <p className="text-xs text-green-700 mt-1">
                            Exact amount will be calculated by the system
                        </p>
                    </div>

                    {/* Submit Button */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                'Submitting...'
                            ) : (
                                <>
                                    <Printer className="w-4 h-4" />
                                    Submit Job
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SubmitPrintJob;
