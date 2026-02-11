import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import POSDashboard from './pages/pos/POSDashboard';
import NewSale from './pages/pos/NewSale';
import Sessions from './pages/pos/Sessions';
import AdminDashboard from './pages/admin/AdminDashboard';
import Services from './pages/admin/Services';
import Users from './pages/admin/Users';
import Reports from './pages/admin/Reports';
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

            {/* Admin Routes */}
            <Route
                path="/admin"
                element={
                    <ProtectedRoute allowedRoles={['admin', 'manager']}>
                        <AdminDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/services"
                element={
                    <ProtectedRoute allowedRoles={['admin', 'manager']}>
                        <Services />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/users"
                element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        <Users />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/reports"
                element={
                    <ProtectedRoute allowedRoles={['admin', 'manager']}>
                        <Reports />
                    </ProtectedRoute>
                }
            />

            {/* Default redirect */}
            <Route
                path="/"
                element={
                    user ? (
                        user.role === 'attendant' ? (
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
            <BrowserRouter>
                <AppRoutes />
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
