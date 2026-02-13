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
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route
                path="/"
                element={<Navigate to="/login" replace />}
            />
            {/* POS Routes - Placeholder for now until we confirm ShiftProvider is safe */}
            <Route
                path="/pos"
                element={
                    <ProtectedRoute>
                        <POSDashboard />
                    </ProtectedRoute>
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
