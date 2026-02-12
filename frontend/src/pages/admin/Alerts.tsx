import React, { useState, useEffect } from 'react';
import {
    CheckCircle,
    Clock,
    Filter,
    RefreshCw,
    Eye,
    X
} from 'lucide-react';
import { alertsApi, Alert, AlertType, AlertSeverity, AlertStatus } from '../../api/alerts';

export const Alerts: React.FC = () => {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);

    // Filters
    const [typeFilter, setTypeFilter] = useState<AlertType | ''>('');
    const [severityFilter, setSeverityFilter] = useState<AlertSeverity | ''>('');
    const [statusFilter, setStatusFilter] = useState<AlertStatus | ''>('');

    // Selected alert for details
    const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
    const [showDetails, setShowDetails] = useState(false);

    // Action modals
    const [showAcknowledgeModal, setShowAcknowledgeModal] = useState(false);
    const [showResolveModal, setShowResolveModal] = useState(false);
    const [actionNotes, setActionNotes] = useState('');

    useEffect(() => {
        loadAlerts();
    }, [page, typeFilter, severityFilter, statusFilter]);

    const loadAlerts = async () => {
        setLoading(true);
        try {
            const response = await alertsApi.list({
                page,
                page_size: pageSize,
                type_filter: typeFilter || undefined,
                severity_filter: severityFilter || undefined,
                status_filter: statusFilter || undefined,
            });
            setAlerts(response.items);
            setTotal(response.total);
        } catch (error) {
            console.error('Error loading alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAcknowledge = async () => {
        if (!selectedAlert) return;

        try {
            await alertsApi.acknowledge(selectedAlert.id, { notes: actionNotes || undefined });
            setShowAcknowledgeModal(false);
            setActionNotes('');
            loadAlerts();
            setShowDetails(false);
        } catch (error) {
            console.error('Error acknowledging alert:', error);
        }
    };

    const handleResolve = async () => {
        if (!selectedAlert || !actionNotes.trim()) return;

        try {
            await alertsApi.resolve(selectedAlert.id, { resolution_notes: actionNotes });
            setShowResolveModal(false);
            setActionNotes('');
            loadAlerts();
            setShowDetails(false);
        } catch (error) {
            console.error('Error resolving alert:', error);
        }
    };

    const handleRunChecks = async () => {
        setLoading(true);
        try {
            const result = await alertsApi.runChecks();
            alert(result.message);
            loadAlerts();
        } catch (error) {
            console.error('Error running checks:', error);
            alert('Error running alert checks');
        } finally {
            setLoading(false);
        }
    };

    const getSeverityColor = (severity: AlertSeverity) => {
        switch (severity) {
            case 'critical': return 'bg-red-100 text-red-800 border-red-300';
            case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
            case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
            case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
            default: return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    const getStatusColor = (status: AlertStatus) => {
        switch (status) {
            case 'open': return 'bg-red-100 text-red-800';
            case 'acknowledged': return 'bg-yellow-100 text-yellow-800';
            case 'resolved': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getTypeLabel = (type: AlertType) => {
        switch (type) {
            case 'void_abuse': return 'Void/Refund Abuse';
            case 'discount_abuse': return 'Discount Abuse';
            case 'cash_discrepancy': return 'Cash Discrepancy';
            case 'inventory_manipulation': return 'Inventory Manipulation';
            case 'price_tampering': return 'Price Tampering';
            default: return type;
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Security Alerts</h1>
                <div className="flex gap-2">
                    <button
                        onClick={loadAlerts}
                        disabled={loading}
                        className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 flex items-center gap-2"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    <button
                        onClick={handleRunChecks}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                        Run Checks Now
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow mb-6">
                <div className="flex items-center gap-2 mb-3">
                    <Filter className="w-5 h-5" />
                    <span className="font-semibold">Filters</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Type</label>
                        <select
                            value={typeFilter}
                            onChange={(e) => setTypeFilter(e.target.value as AlertType | '')}
                            className="w-full border rounded px-3 py-2"
                        >
                            <option value="">All Types</option>
                            <option value="void_abuse">Void/Refund Abuse</option>
                            <option value="discount_abuse">Discount Abuse</option>
                            <option value="cash_discrepancy">Cash Discrepancy</option>
                            <option value="inventory_manipulation">Inventory Manipulation</option>
                            <option value="price_tampering">Price Tampering</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Severity</label>
                        <select
                            value={severityFilter}
                            onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity | '')}
                            className="w-full border rounded px-3 py-2"
                        >
                            <option value="">All Severities</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Status</label>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value as AlertStatus | '')}
                            className="w-full border rounded px-3 py-2"
                        >
                            <option value="">All Statuses</option>
                            <option value="open">Open</option>
                            <option value="acknowledged">Acknowledged</option>
                            <option value="resolved">Resolved</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Alerts List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center">Loading...</div>
                ) : alerts.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">No alerts found</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Severity</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Type</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Message</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Created</th>
                                    <th className="px-4 py-3 text-left text-sm font-semibold">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {alerts.map((alert) => (
                                    <tr key={alert.id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${getSeverityColor(alert.severity)}`}>
                                                {alert.severity}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm">{getTypeLabel(alert.type)}</td>
                                        <td className="px-4 py-3 text-sm">{alert.message}</td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${getStatusColor(alert.status)}`}>
                                                {alert.status}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {new Date(alert.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => {
                                                        setSelectedAlert(alert);
                                                        setShowDetails(true);
                                                    }}
                                                    className="text-blue-600 hover:text-blue-800"
                                                    title="View Details"
                                                >
                                                    <Eye className="w-4 h-4" />
                                                </button>
                                                {alert.status === 'open' && (
                                                    <button
                                                        onClick={() => {
                                                            setSelectedAlert(alert);
                                                            setShowAcknowledgeModal(true);
                                                        }}
                                                        className="text-yellow-600 hover:text-yellow-800"
                                                        title="Acknowledge"
                                                    >
                                                        <Clock className="w-4 h-4" />
                                                    </button>
                                                )}
                                                {alert.status !== 'resolved' && (
                                                    <button
                                                        onClick={() => {
                                                            setSelectedAlert(alert);
                                                            setShowResolveModal(true);
                                                        }}
                                                        className="text-green-600 hover:text-green-800"
                                                        title="Resolve"
                                                    >
                                                        <CheckCircle className="w-4 h-4" />
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

                {/* Pagination */}
                {total > pageSize && (
                    <div className="px-4 py-3 border-t flex justify-between items-center">
                        <div className="text-sm text-gray-600">
                            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total}
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-3 py-1 border rounded disabled:opacity-50"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPage(p => p + 1)}
                                disabled={page * pageSize >= total}
                                className="px-3 py-1 border rounded disabled:opacity-50"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Details Modal */}
            {showDetails && selectedAlert && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-start mb-4">
                            <h2 className="text-xl font-bold">Alert Details</h2>
                            <button onClick={() => setShowDetails(false)}>
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="font-semibold">Severity:</label>
                                <span className={`ml-2 px-2 py-1 rounded text-xs font-semibold uppercase ${getSeverityColor(selectedAlert.severity)}`}>
                                    {selectedAlert.severity}
                                </span>
                            </div>
                            <div>
                                <label className="font-semibold">Type:</label>
                                <span className="ml-2">{getTypeLabel(selectedAlert.type)}</span>
                            </div>
                            <div>
                                <label className="font-semibold">Status:</label>
                                <span className={`ml-2 px-2 py-1 rounded text-xs font-semibold uppercase ${getStatusColor(selectedAlert.status)}`}>
                                    {selectedAlert.status}
                                </span>
                            </div>
                            <div>
                                <label className="font-semibold">Message:</label>
                                <p className="mt-1">{selectedAlert.message}</p>
                            </div>
                            {selectedAlert.description && (
                                <div>
                                    <label className="font-semibold">Description:</label>
                                    <p className="mt-1 whitespace-pre-wrap">{selectedAlert.description}</p>
                                </div>
                            )}
                            {selectedAlert.related_entity && (
                                <div>
                                    <label className="font-semibold">Related Entity:</label>
                                    <pre className="mt-1 bg-gray-100 p-2 rounded text-sm overflow-x-auto">
                                        {JSON.stringify(selectedAlert.related_entity, null, 2)}
                                    </pre>
                                </div>
                            )}
                            {selectedAlert.metadata && (
                                <div>
                                    <label className="font-semibold">Metadata:</label>
                                    <pre className="mt-1 bg-gray-100 p-2 rounded text-sm overflow-x-auto">
                                        {JSON.stringify(selectedAlert.metadata, null, 2)}
                                    </pre>
                                </div>
                            )}
                            <div>
                                <label className="font-semibold">Created:</label>
                                <span className="ml-2">{new Date(selectedAlert.created_at).toLocaleString()}</span>
                            </div>
                            {selectedAlert.acknowledged_at && (
                                <div>
                                    <label className="font-semibold">Acknowledged:</label>
                                    <span className="ml-2">{new Date(selectedAlert.acknowledged_at).toLocaleString()}</span>
                                </div>
                            )}
                            {selectedAlert.resolved_at && (
                                <div>
                                    <label className="font-semibold">Resolved:</label>
                                    <span className="ml-2">{new Date(selectedAlert.resolved_at).toLocaleString()}</span>
                                </div>
                            )}
                            {selectedAlert.resolution_notes && (
                                <div>
                                    <label className="font-semibold">Resolution Notes:</label>
                                    <p className="mt-1">{selectedAlert.resolution_notes}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Acknowledge Modal */}
            {showAcknowledgeModal && selectedAlert && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                        <h2 className="text-xl font-bold mb-4">Acknowledge Alert</h2>
                        <p className="mb-4">Are you sure you want to acknowledge this alert?</p>
                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Notes (optional)</label>
                            <textarea
                                value={actionNotes}
                                onChange={(e) => setActionNotes(e.target.value)}
                                className="w-full border rounded px-3 py-2"
                                rows={3}
                                placeholder="Add any notes..."
                            />
                        </div>
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => {
                                    setShowAcknowledgeModal(false);
                                    setActionNotes('');
                                }}
                                className="px-4 py-2 border rounded"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAcknowledge}
                                className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                            >
                                Acknowledge
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Resolve Modal */}
            {showResolveModal && selectedAlert && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                        <h2 className="text-xl font-bold mb-4">Resolve Alert</h2>
                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Resolution Notes *</label>
                            <textarea
                                value={actionNotes}
                                onChange={(e) => setActionNotes(e.target.value)}
                                className="w-full border rounded px-3 py-2"
                                rows={4}
                                placeholder="Describe how this issue was resolved..."
                                required
                            />
                        </div>
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => {
                                    setShowResolveModal(false);
                                    setActionNotes('');
                                }}
                                className="px-4 py-2 border rounded"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleResolve}
                                disabled={!actionNotes.trim()}
                                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                            >
                                Resolve
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
