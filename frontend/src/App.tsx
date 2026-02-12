import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ShiftProvider } from './context/ShiftContext';
import Login from './pages/Login';
import POSDashboard from './pages/pos/POSDashboard';
import NewSale from './pages/pos/NewSale';
import Sessions from './pages/pos/Sessions';
import Transactions from './pages/pos/Transactions';
import PrintJobQueue from './pages/pos/PrintJobQueue';
import AdminDashboard from './pages/admin/AdminDashboard';
import Services from './pages/admin/Services';
import Inventory from './pages/admin/Inventory';
import Users from './pages/admin/Users';
import Reports from './pages/admin/Reports';
import MpesaInbox from './pages/admin/MpesaInbox';
import MpesaReconciliation from './pages/admin/MpesaReconciliation';
import './index.css';

const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: string[] }> = ({
    children,
    allowedRoles,
}) => {
    const { user, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl">Loading...</div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
        return <Navigate to="/" replace />;
    }

    return <>{children}</>;
};

function AppRoutes() {
    const { user } = useAuth();

    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            {/* POS Routes */}
            <Route
                path="/pos"
                element={
                    <ProtectedRoute>
                        <POSDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/pos/new-sale"
                element={
                    <ProtectedRoute>
                        <NewSale />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/pos/sessions"
                element={
                    <ProtectedRoute>
                        <Sessions />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/pos/transactions"
                element={
                    <ProtectedRoute>
                        <Transactions />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/pos/print-queue"
                element={
                    <ProtectedRoute>
                        <PrintJobQueue />
                    </ProtectedRoute>
                }
            />

            {/* Admin Routes */}
            <Route
                path="/admin"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
                        <AdminDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/services"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
                        <Services />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/users"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN']}>
                        <Users />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/inventory"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
                        <Inventory />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/reports"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
                        <Reports />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/mpesa-inbox"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
                        <MpesaInbox />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/mpesa-reconciliation"
                element={
                    <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
                        <MpesaReconciliation />
                    </ProtectedRoute>
                }
            />

            {/* Default redirect */}
            <Route
                path="/"
                element={
                    user ? (
                        user.role === 'ATTENDANT' ? (
                            <Navigate to="/pos" replace />
                        ) : (
                            <Navigate to="/admin" replace />
                        )
                    ) : (
                        <Navigate to="/login" replace />
                    )
                }
            />
        </Routes>
    );
}

function App() {
    return (
        <AuthProvider>
            <ShiftProvider>
                <BrowserRouter>
                    <AppRoutes />
                </BrowserRouter>
            </ShiftProvider>
        </AuthProvider>
    );
}

export default App;
