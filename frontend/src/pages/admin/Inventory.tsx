import React, { useState, useEffect } from 'react';
import { inventoryApi, InventoryItem, StockMovement } from '../../api/inventory';
import { Plus, Search, Filter, AlertTriangle, ArrowUp, ArrowDown, History, Edit2 } from 'lucide-react';

const Inventory: React.FC = () => {
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showLowStockOnly, setShowLowStockOnly] = useState(false);

    // Modal states
    const [showItemModal, setShowItemModal] = useState(false);
    const [showAdjustModal, setShowAdjustModal] = useState(false);
    const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
    const [selectedItemForAdjust, setSelectedItemForAdjust] = useState<InventoryItem | null>(null);

    // Form states
    const [itemForm, setItemForm] = useState({ name: '', unit: 'pcs', min_stock_level: 0, unit_cost: 0, current_stock: 0 });
    const [adjustForm, setAdjustForm] = useState({ quantity: 0, type: 'purchase' as 'purchase' | 'adjustment', notes: '' });

    useEffect(() => {
        loadItems();
    }, [showLowStockOnly]);

    const loadItems = async () => {
        setLoading(true);
        try {
            const data = await inventoryApi.getAll(showLowStockOnly);
            setItems(data);
        } catch (error) {
            console.error('Error loading inventory:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveItem = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingItem) {
                await inventoryApi.update(editingItem.id, itemForm);
            } else {
                await inventoryApi.create(itemForm);
            }
            setShowItemModal(false);
            setEditingItem(null);
            setItemForm({ name: '', unit: 'pcs', min_stock_level: 0, unit_cost: 0, current_stock: 0 });
            loadItems();
        } catch (error) {
            console.error('Error saving item:', error);
            alert('Failed to save item');
        }
    };

    const handleAdjustStock = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedItemForAdjust) return;

        try {
            await inventoryApi.adjustStock({
                item_id: selectedItemForAdjust.id,
                movement_type: adjustForm.type,
                quantity: adjustForm.quantity, // Backend expects positive for purchase, logic handles sign based on type? 
                // Wait, backend logic:
                // PURCHASE: += qty
                // USAGE: -= qty
                // ADJUSTMENT: += qty (so negative needed for reduction)
                // Let's ensure we send positive for purchase/usage and signed for adjustment if needed
                // Backend: "ADJUSTMENT: item.current_stock += adjustment.quantity"

                notes: adjustForm.notes
            });
            setShowAdjustModal(false);
            setSelectedItemForAdjust(null);
            setAdjustForm({ quantity: 0, type: 'purchase', notes: '' });
            loadItems();
        } catch (error) {
            console.error('Error adjusting stock:', error);
            alert('Failed to adjust stock');
        }
    };

    const openEditModal = (item: InventoryItem) => {
        setEditingItem(item);
        setItemForm({
            name: item.name,
            unit: item.unit,
            min_stock_level: item.min_stock_level,
            unit_cost: item.unit_cost,
            current_stock: item.current_stock
        });
        setShowItemModal(true);
    };

    const openAdjustModal = (item: InventoryItem) => {
        setSelectedItemForAdjust(item);
        setAdjustForm({ quantity: 0, type: 'purchase', notes: '' });
        setShowAdjustModal(true);
    };

    const filteredItems = items.filter(item =>
        item.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Inventory Management</h1>
                    <p className="text-gray-600">Track stock levels and consumables</p>
                </div>
                <button
                    onClick={() => { setEditingItem(null); setItemForm({ name: '', unit: 'pcs', min_stock_level: 0, unit_cost: 0, current_stock: 0 }); setShowItemModal(true); }}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus size={20} />
                    Add Item
                </button>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-6">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Search items..."
                        className="input pl-10 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <button
                    onClick={() => setShowLowStockOnly(!showLowStockOnly)}
                    className={`btn flex items-center gap-2 ${showLowStockOnly ? 'btn-danger' : 'btn-secondary'}`}
                >
                    <AlertTriangle size={20} />
                    {showLowStockOnly ? 'Show All Items' : 'Show Low Stock Only'}
                </button>
            </div>

            {/* Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock Level</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit Cost</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reorder Level</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan={5} className="p-4 text-center">Loading...</td></tr>
                        ) : filteredItems.length === 0 ? (
                            <tr><td colSpan={5} className="p-4 text-center">No items found</td></tr>
                        ) : (
                            filteredItems.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="font-medium text-gray-900">{item.name}</div>
                                        <div className="text-sm text-gray-500">Unit: {item.unit}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className={`flex items-center gap-2 font-semibold ${item.current_stock <= item.min_stock_level ? 'text-red-600' : 'text-green-600'}`}>
                                            {item.current_stock}
                                            {item.current_stock <= item.min_stock_level && <AlertTriangle size={16} />}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        KES {item.unit_cost.toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                                        {item.min_stock_level}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => openAdjustModal(item)}
                                            className="text-blue-600 hover:text-blue-900 mr-4"
                                            title="Adjust Stock"
                                        >
                                            <History size={18} />
                                        </button>
                                        <button
                                            onClick={() => openEditModal(item)}
                                            className="text-gray-600 hover:text-gray-900"
                                            title="Edit Item"
                                        >
                                            <Edit2 size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Item Modal (Add/Edit) */}
            {showItemModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">{editingItem ? 'Edit Item' : 'New Inventory Item'}</h2>
                        <form onSubmit={handleSaveItem}>
                            <div className="space-y-4">
                                <div>
                                    <label className="label">Item Name</label>
                                    <input type="text" className="input w-full" value={itemForm.name} onChange={e => setItemForm({ ...itemForm, name: e.target.value })} required />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Unit (e.g., pcs, ream)</label>
                                        <input type="text" className="input w-full" value={itemForm.unit} onChange={e => setItemForm({ ...itemForm, unit: e.target.value })} required />
                                    </div>
                                    <div>
                                        <label className="label">Unit Cost</label>
                                        <input type="number" step="0.01" className="input w-full" value={itemForm.unit_cost} onChange={e => setItemForm({ ...itemForm, unit_cost: parseFloat(e.target.value) })} required />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Current Stock</label>
                                        <input type="number" step="0.01" className="input w-full" value={itemForm.current_stock} onChange={e => setItemForm({ ...itemForm, current_stock: parseFloat(e.target.value) })} required disabled={!!editingItem} />
                                        {editingItem && <p className="text-xs text-gray-500 mt-1">Use Adjustment to change stock</p>}
                                    </div>
                                    <div>
                                        <label className="label">Reorder Level</label>
                                        <input type="number" step="0.01" className="input w-full" value={itemForm.min_stock_level} onChange={e => setItemForm({ ...itemForm, min_stock_level: parseFloat(e.target.value) })} required />
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-end gap-2 mt-6">
                                <button type="button" onClick={() => setShowItemModal(false)} className="btn btn-secondary">Cancel</button>
                                <button type="submit" className="btn btn-primary">Save Item</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Adjustment Modal */}
            {showAdjustModal && selectedItemForAdjust && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Adjust Stock: {selectedItemForAdjust.name}</h2>
                        <form onSubmit={handleAdjustStock}>
                            <div className="space-y-4">
                                <div>
                                    <label className="label">Adjustment Type</label>
                                    <select
                                        className="input w-full"
                                        value={adjustForm.type}
                                        onChange={e => setAdjustForm({ ...adjustForm, type: e.target.value as any })}
                                    >
                                        <option value="purchase">Restock (Purchase)</option>
                                        <option value="usage">Usage / Damaged (Reduce)</option>
                                        <option value="adjustment">Correction (+/-)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label">Quantity</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        className="input w-full"
                                        value={adjustForm.quantity}
                                        onChange={e => setAdjustForm({ ...adjustForm, quantity: parseFloat(e.target.value) })}
                                        required
                                        placeholder={adjustForm.type === 'adjustment' ? 'Use negative for reduction' : 'Positive value'}
                                    />
                                    {adjustForm.type === 'usage' && <p className="text-xs text-gray-500">Enter positive amount to remove</p>}
                                </div>
                                <div>
                                    <label className="label">Notes / Reason</label>
                                    <textarea
                                        className="input w-full"
                                        value={adjustForm.notes}
                                        onChange={e => setAdjustForm({ ...adjustForm, notes: e.target.value })}
                                        required
                                        rows={3}
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end gap-2 mt-6">
                                <button type="button" onClick={() => setShowAdjustModal(false)} className="btn btn-secondary">Cancel</button>
                                <button type="submit" className="btn btn-primary">Confirm Adjustment</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Inventory;
