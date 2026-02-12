import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    Printer,
    CheckCircle,
    XCircle,
    Clock,
    FileText,
    AlertCircle,
    Loader2
} from 'lucide-react';
import { printJobsApi, PrintJob } from '../../api/printJobs';
import { format } from 'date-fns';

const PrintJobQueue: React.FC = () => {
    const [jobs, setJobs] = useState<PrintJob[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [pendingCount, setPendingCount] = useState(0);
    const [approvedCount, setApprovedCount] = useState(0);
    const [selectedJob, setSelectedJob] = useState<PrintJob | null>(null);
    const [showRejectDialog, setShowRejectDialog] = useState(false);
    const [rejectionReason, setRejectionReason] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        loadJobs();
        // Poll for updates every 10 seconds
        const interval = setInterval(loadJobs, 10000);
        return () => clearInterval(interval);
    }, [statusFilter]);

    const loadJobs = async () => {
        try {
            const data = await printJobsApi.list({
                status_filter: statusFilter || undefined,
                page_size: 100,
            });
            setJobs(data.items);
            setPendingCount(data.pending_count);
            setApprovedCount(data.approved_count);
        } catch (error) {
            console.error('Error loading print jobs:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (job: PrintJob) => {
        if (!confirm(`Approve print job ${job.job_number}?\n\nThis will create a transaction and reserve stock.`)) {
            return;
        }

        setActionLoading(true);
        try {
            await printJobsApi.approve(job.id);
            alert(`Print job ${job.job_number} approved!`);
            loadJobs();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to approve job');
        } finally {
            setActionLoading(false);
        }
    };

    const handleReject = async () => {
        if (!selectedJob || !rejectionReason.trim()) {
            alert('Please provide a rejection reason');
            return;
        }

        setActionLoading(true);
        try {
            await printJobsApi.reject(selectedJob.id, rejectionReason);
            alert(`Print job ${selectedJob.job_number} rejected`);
            setShowRejectDialog(false);
            setRejectionReason('');
            setSelectedJob(null);
            loadJobs();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to reject job');
        } finally {
            setActionLoading(false);
        }
    };

    const handleMarkPrinted = async (job: PrintJob) => {
        if (!confirm(`Mark job ${job.job_number} as printed?\n\nThis will finalize stock deduction.`)) {
            return;
        }

        setActionLoading(true);
        try {
            await printJobsApi.markPrinted(job.id);
            alert(`Print job ${job.job_number} marked as printed!`);
            loadJobs();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to mark as printed');
        } finally {
            setActionLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const badges = {
            pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'Pending' },
            approved: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle, label: 'Approved' },
            printed: { color: 'bg-green-100 text-green-800', icon: Printer, label: 'Printed' },
            rejected: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Rejected' },
            cancelled: { color: 'bg-gray-100 text-gray-800', icon: XCircle, label: 'Cancelled' },
        };

        const badge = badges[status as keyof typeof badges] || badges.pending;
        const Icon = badge.icon;

        return (
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
                <Icon className="w-3 h-3" />
                {badge.label}
            </span>
        );
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link to="/pos" className="btn btn-secondary">
                                ← Back to POS
                            </Link>
                            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                <Printer className="w-7 h-7" />
                                Print Job Queue
                            </h1>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-sm">
                                <span className="font-medium text-yellow-600">{pendingCount} Pending</span>
                                <span className="mx-2">•</span>
                                <span className="font-medium text-blue-600">{approvedCount} Approved</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Filter Tabs */}
                <div className="bg-white rounded-lg shadow mb-6">
                    <div className="border-b border-gray-200">
                        <nav className="flex -mb-px">
                            {[
                                { value: '', label: 'All' },
                                { value: 'pending', label: 'Pending' },
                                { value: 'approved', label: 'Approved' },
                                { value: 'printed', label: 'Printed' },
                                { value: 'rejected', label: 'Rejected' },
                            ].map((tab) => (
                                <button
                                    key={tab.value}
                                    onClick={() => setStatusFilter(tab.value)}
                                    className={`px-6 py-3 text-sm font-medium border-b-2 ${statusFilter === tab.value
                                            ? 'border-green-600 text-green-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* Jobs List */}
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-green-600" />
                    </div>
                ) : jobs.length === 0 ? (
                    <div className="bg-white rounded-lg shadow p-12 text-center">
                        <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600">No print jobs found</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {jobs.map((job) => (
                            <div key={job.id} className="bg-white rounded-lg shadow p-6">
                                {/* Job Header */}
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900">
                                            {job.job_number}
                                        </h3>
                                        <p className="text-sm text-gray-600">{job.requested_by}</p>
                                    </div>
                                    {getStatusBadge(job.status)}
                                </div>

                                {/* Job Details */}
                                <div className="space-y-2 mb-4">
                                    {job.description && (
                                        <p className="text-sm text-gray-700">{job.description}</p>
                                    )}
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-600">B&W Pages:</span>
                                        <span className="font-medium">{job.pages_bw}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-600">Color Pages:</span>
                                        <span className="font-medium">{job.pages_color}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm pt-2 border-t">
                                        <span className="text-gray-900 font-medium">Total:</span>
                                        <span className="text-lg font-bold text-green-600">
                                            KES {job.total_amount.toLocaleString()}
                                        </span>
                                    </div>
                                </div>

                                {/* Timestamps */}
                                <div className="text-xs text-gray-500 mb-4">
                                    <p>Submitted: {format(new Date(job.created_at), 'MMM dd, HH:mm')}</p>
                                    {job.approved_at && (
                                        <p>Approved: {format(new Date(job.approved_at), 'MMM dd, HH:mm')}</p>
                                    )}
                                    {job.printed_at && (
                                        <p>Printed: {format(new Date(job.printed_at), 'MMM dd, HH:mm')}</p>
                                    )}
                                </div>

                                {/* Rejection Reason */}
                                {job.status === 'rejected' && job.rejection_reason && (
                                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
                                        <p className="text-xs font-medium text-red-800 mb-1">Rejection Reason:</p>
                                        <p className="text-sm text-red-700">{job.rejection_reason}</p>
                                    </div>
                                )}

                                {/* Action Buttons */}
                                {job.status === 'pending' && (
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleApprove(job)}
                                            disabled={actionLoading}
                                            className="flex-1 btn btn-primary py-2 text-sm disabled:opacity-50"
                                        >
                                            <CheckCircle className="w-4 h-4 mr-1" />
                                            Approve
                                        </button>
                                        <button
                                            onClick={() => {
                                                setSelectedJob(job);
                                                setShowRejectDialog(true);
                                            }}
                                            disabled={actionLoading}
                                            className="flex-1 btn btn-secondary py-2 text-sm disabled:opacity-50"
                                        >
                                            <XCircle className="w-4 h-4 mr-1" />
                                            Reject
                                        </button>
                                    </div>
                                )}

                                {job.status === 'approved' && (
                                    <button
                                        onClick={() => handleMarkPrinted(job)}
                                        disabled={actionLoading}
                                        className="w-full btn btn-primary py-2 text-sm disabled:opacity-50"
                                    >
                                        <Printer className="w-4 h-4 mr-1" />
                                        Mark as Printed
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>

            {/* Reject Dialog */}
            {showRejectDialog && selectedJob && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <AlertCircle className="w-6 h-6 text-red-600" />
                            <h3 className="text-lg font-semibold text-gray-900">
                                Reject Print Job
                            </h3>
                        </div>

                        <p className="text-sm text-gray-600 mb-4">
                            Job: <span className="font-medium">{selectedJob.job_number}</span>
                        </p>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Rejection Reason *
                            </label>
                            <textarea
                                value={rejectionReason}
                                onChange={(e) => setRejectionReason(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                rows={3}
                                placeholder="Enter reason for rejection..."
                                required
                            />
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => {
                                    setShowRejectDialog(false);
                                    setRejectionReason('');
                                    setSelectedJob(null);
                                }}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleReject}
                                disabled={!rejectionReason.trim() || actionLoading}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                            >
                                {actionLoading ? 'Rejecting...' : 'Reject Job'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PrintJobQueue;
