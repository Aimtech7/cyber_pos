import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { reportsApi } from '../../api/reports';
import { ArrowLeft, Calendar } from 'lucide-react';

const Reports: React.FC = () => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [salesReport, setSalesReport] = useState<any>(null);
    const [servicePerformance, setServicePerformance] = useState<any[]>([]);
    const [attendantPerformance, setAttendantPerformance] = useState<any[]>([]);
    const [profitReport, setProfitReport] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleGenerateReports = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            const [sales, services, attendants, profit] = await Promise.all([
                reportsApi.getSalesReport(startDate, endDate),
                reportsApi.getServicePerformance(startDate, endDate),
                reportsApi.getAttendantPerformance(startDate, endDate),
                reportsApi.getProfitReport(startDate, endDate),
            ]);

            setSalesReport(sales);
            setServicePerformance(services);
            setAttendantPerformance(attendants);
            setProfitReport(profit);
        } catch (error) {
            console.error('Error generating reports:', error);
            alert('Failed to generate reports');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center gap-4">
                        <Link to="/admin" className="btn btn-secondary">
                            <ArrowLeft className="w-4 h-4" />
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Date Range Selector */}
                <div className="card mb-6">
                    <form onSubmit={handleGenerateReports} className="flex flex-wrap gap-4 items-end">
                        <div className="flex-1 min-w-[200px]">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Start Date
                            </label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="input"
                                required
                            />
                        </div>

                        <div className="flex-1 min-w-[200px]">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                End Date
                            </label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="input"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
                        >
                            <Calendar className="w-4 h-4" />
                            {isLoading ? 'Generating...' : 'Generate Reports'}
                        </button>
                    </form>
                </div>

                {/* Sales Report */}
                {salesReport && (
                    <div className="card mb-6">
                        <h2 className="text-xl font-semibold mb-4">Sales Summary</h2>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Total Sales</p>
                                <p className="text-2xl font-bold text-gray-900">
                                    KES {salesReport.total_sales?.toFixed(2) || '0.00'}
                                </p>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Cash</p>
                                <p className="text-2xl font-bold text-green-600">
                                    KES {salesReport.total_cash?.toFixed(2) || '0.00'}
                                </p>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">M-Pesa</p>
                                <p className="text-2xl font-bold text-blue-600">
                                    KES {salesReport.total_mpesa?.toFixed(2) || '0.00'}
                                </p>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Transactions</p>
                                <p className="text-2xl font-bold text-gray-900">
                                    {salesReport.transaction_count || 0}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Profit Report */}
                {profitReport && (
                    <div className="card mb-6">
                        <h2 className="text-xl font-semibold mb-4">Profit Analysis</h2>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Revenue</p>
                                <p className="text-2xl font-bold text-green-600">
                                    KES {profitReport.total_revenue?.toFixed(2) || '0.00'}
                                </p>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Expenses</p>
                                <p className="text-2xl font-bold text-red-600">
                                    KES {profitReport.total_expenses?.toFixed(2) || '0.00'}
                                </p>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Gross Profit</p>
                                <p className="text-2xl font-bold text-primary-600">
                                    KES {profitReport.gross_profit?.toFixed(2) || '0.00'}
                                </p>
                            </div>
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <p className="text-sm text-gray-600">Profit Margin</p>
                                <p className="text-2xl font-bold text-gray-900">
                                    {profitReport.profit_margin?.toFixed(1) || '0.0'}%
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Service Performance */}
                {servicePerformance.length > 0 && (
                    <div className="card mb-6">
                        <h2 className="text-xl font-semibold mb-4">Service Performance</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-3 px-4">Service</th>
                                        <th className="text-right py-3 px-4">Quantity Sold</th>
                                        <th className="text-right py-3 px-4">Revenue</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {servicePerformance.map((service, index) => (
                                        <tr key={index} className="border-b hover:bg-gray-50">
                                            <td className="py-3 px-4 font-medium">{service.service_name}</td>
                                            <td className="py-3 px-4 text-right">{service.quantity_sold}</td>
                                            <td className="py-3 px-4 text-right font-semibold">
                                                KES {parseFloat(service.revenue).toFixed(2)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Attendant Performance */}
                {attendantPerformance.length > 0 && (
                    <div className="card">
                        <h2 className="text-xl font-semibold mb-4">Attendant Performance</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-3 px-4">Attendant</th>
                                        <th className="text-right py-3 px-4">Transactions</th>
                                        <th className="text-right py-3 px-4">Total Sales</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {attendantPerformance.map((attendant, index) => (
                                        <tr key={index} className="border-b hover:bg-gray-50">
                                            <td className="py-3 px-4 font-medium">{attendant.attendant_name}</td>
                                            <td className="py-3 px-4 text-right">{attendant.transaction_count}</td>
                                            <td className="py-3 px-4 text-right font-semibold">
                                                KES {parseFloat(attendant.total_sales).toFixed(2)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default Reports;
