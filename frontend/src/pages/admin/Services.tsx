import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { servicesApi } from '../../api/services';
import { Service } from '../../types';
import { ArrowLeft, Plus, Edit, Trash2 } from 'lucide-react';

const Services: React.FC = () => {
    const [services, setServices] = useState<Service[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [editingService, setEditingService] = useState<Service | null>(null);
    const [formData, setFormData] = useState({
        name: '',
        pricing_mode: 'per_page' as 'per_page' | 'per_minute' | 'per_job' | 'bundle',
        base_price: '',
        description: '',
    });

    useEffect(() => {
        loadServices();
    }, []);

    const loadServices = async () => {
        try {
            const data = await servicesApi.list(false); // Show all services
            setServices(data);
        } catch (error) {
            console.error('Error loading services:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const data = {
                ...formData,
                base_price: parseFloat(formData.base_price),
            };

            if (editingService) {
                await servicesApi.update(editingService.id, data);
            } else {
                await servicesApi.create(data);
            }

            setShowForm(false);
            setEditingService(null);
            setFormData({ name: '', pricing_mode: 'per_page', base_price: '', description: '' });
            loadServices();
        } catch (error) {
            console.error('Error saving service:', error);
            alert('Failed to save service');
        }
    };

    const handleEdit = (service: Service) => {
        setEditingService(service);
        setFormData({
            name: service.name,
            pricing_mode: service.pricing_mode,
            base_price: service.base_price.toString(),
            description: service.description || '',
        });
        setShowForm(true);
    };

    const handleDelete = async (id: string) => {
        if (confirm('Are you sure you want to delete this service?')) {
            try {
                await servicesApi.delete(id);
                loadServices();
            } catch (error) {
                console.error('Error deleting service:', error);
                alert('Failed to delete service');
            }
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link to="/admin" className="btn btn-secondary">
                                <ArrowLeft className="w-4 h-4" />
                            </Link>
                            <h1 className="text-2xl font-bold text-gray-900">Services Management</h1>
                        </div>
                        <button onClick={() => setShowForm(true)} className="btn btn-primary flex items-center gap-2">
                            <Plus className="w-4 h-4" />
                            Add Service
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {showForm && (
                    <div className="card mb-6">
                        <h2 className="text-xl font-semibold mb-4">
                            {editingService ? 'Edit Service' : 'New Service'}
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Service Name
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="input"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Pricing Mode
                                    </label>
                                    <select
                                        value={formData.pricing_mode}
                                        onChange={(e) => setFormData({ ...formData, pricing_mode: e.target.value as any })}
                                        className="input"
                                    >
                                        <option value="per_page">Per Page</option>
                                        <option value="per_minute">Per Minute</option>
                                        <option value="per_job">Per Job</option>
                                        <option value="bundle">Bundle</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Base Price (KES)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={formData.base_price}
                                        onChange={(e) => setFormData({ ...formData, base_price: e.target.value })}
                                        className="input"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Description
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        className="input"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <button type="submit" className="btn btn-primary">
                                    {editingService ? 'Update' : 'Create'} Service
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowForm(false);
                                        setEditingService(null);
                                        setFormData({ name: '', pricing_mode: 'per_page', base_price: '', description: '' });
                                    }}
                                    className="btn btn-secondary"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                <div className="card">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-3 px-4">Name</th>
                                    <th className="text-left py-3 px-4">Pricing Mode</th>
                                    <th className="text-left py-3 px-4">Base Price</th>
                                    <th className="text-left py-3 px-4">Status</th>
                                    <th className="text-right py-3 px-4">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {services.map((service) => (
                                    <tr key={service.id} className="border-b hover:bg-gray-50">
                                        <td className="py-3 px-4 font-medium">{service.name}</td>
                                        <td className="py-3 px-4 capitalize">{service.pricing_mode.replace('_', ' ')}</td>
                                        <td className="py-3 px-4">KES {parseFloat(service.base_price.toString()).toFixed(2)}</td>
                                        <td className="py-3 px-4">
                                            <span
                                                className={`px-2 py-1 rounded-full text-xs ${service.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                    }`}
                                            >
                                                {service.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-right">
                                            <button
                                                onClick={() => handleEdit(service)}
                                                className="text-primary-600 hover:text-primary-700 mr-3"
                                            >
                                                <Edit className="w-4 h-4 inline" />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(service.id)}
                                                className="text-red-600 hover:text-red-700"
                                            >
                                                <Trash2 className="w-4 h-4 inline" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Services;
