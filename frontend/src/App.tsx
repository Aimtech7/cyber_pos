import React from 'react';
import './index.css';

// import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
// import { AuthProvider, useAuth } from './context/AuthContext';
// import { ShiftProvider } from './context/ShiftContext';
// import Login from './pages/Login';
// import POSDashboard from './pages/pos/POSDashboard';
// import NewSale from './pages/pos/NewSale';
// import Sessions from './pages/pos/Sessions';
// import Transactions from './pages/pos/Transactions';
// import PrintJobQueue from './pages/pos/PrintJobQueue';
// import AdminDashboard from './pages/admin/AdminDashboard';
// import { Services } from './pages/admin/Services';
// import { Inventory } from './pages/admin/Inventory';
// import { Users } from './pages/admin/Users';
// import { Reports } from './pages/admin/Reports';
// import { MpesaInbox } from './pages/admin/MpesaInbox';
// import { MpesaReconciliation } from './pages/admin/MpesaReconciliation';
// import { Customers } from './pages/admin/Customers';
// import { Invoices } from './pages/admin/Invoices';
// import { Alerts } from './pages/admin/Alerts';
// import { OfflineQueue } from './pages/pos/OfflineQueue';
// import { OfflineProvider } from './context/OfflineContext';
// import { OfflineBanner } from './components/OfflineBanner';

// const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: string[] }> = ({
//     children,
//     allowedRoles,
// }) => {
//     const { user, isLoading } = useAuth();

//     if (isLoading) {
//         return (
//             <div className="flex items-center justify-center min-h-screen">
//                 <div className="text-xl">Loading...</div>
//             </div>
//         );
//     }

//     if (!user) {
//         return <Navigate to="/login" replace />;
//     }

//     if (allowedRoles && !allowedRoles.includes(user.role)) {
//         return <Navigate to="/" replace />;
//     }

//     return <>{children}</>;
// };

// function AppRoutes() {
//     const { user } = useAuth();

//     return (
//         <Routes>
//             <Route path="/login" element={<Login />} />

//             {/* POS Routes */}
//             <Route
//                 path="/pos"
//                 element={
//                     <ProtectedRoute>
//                         <POSDashboard />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/pos/new-sale"
//                 element={
//                     <ProtectedRoute>
//                         <NewSale />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/pos/sessions"
//                 element={
//                     <ProtectedRoute>
//                         <Sessions />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/pos/transactions"
//                 element={
//                     <ProtectedRoute>
//                         <Transactions />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/pos/print-queue"
//                 element={
//                     <ProtectedRoute>
//                         <PrintJobQueue />
//                     </ProtectedRoute>
//                 }
//             />

//             {/* Admin Routes */}
//             <Route
//                 path="/admin"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <AdminDashboard />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/services"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <Services />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/users"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN']}>
//                         <Users />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/inventory"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <Inventory />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/reports"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <Reports />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/mpesa-inbox"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <MpesaInbox />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/mpesa-reconciliation"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <MpesaReconciliation />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/customers"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <Customers />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/invoices"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <Invoices />
//                     </ProtectedRoute>
//                 }
//             />
//             <Route
//                 path="/admin/alerts"
//                 element={
//                     <ProtectedRoute allowedRoles={['ADMIN', 'MANAGER']}>
//                         <Alerts />
//                     </ProtectedRoute>
//                 }
//             />

//             {/* Default redirect */}
//             <Route
//                 path="/"
//                 element={
//                     user ? (
//                         user.role === 'ATTENDANT' ? (
//                             <Navigate to="/pos" replace />
//                         ) : (
//                             <Navigate to="/admin" replace />
//                         )
//                     ) : (
//                         <Navigate to="/login" replace />
//                     )
//                 }
//             />
//             {/* 
//             <Route
//                 path="/pos/offline-queue"
//                 element={
//                     <ProtectedRoute>
//                         <OfflineQueue />
//                     </ProtectedRoute>
//                 }
//             /> 
//             */}
//         </Routes>
//     );
// }

function App() {
    return (
        <div className="p-10 text-center">
            <h1 className="text-xl font-bold text-blue-600">Step 1: Imports Disabled</h1>
            <p>If you see this, the crash is caused by one of the imported files.</p>
        </div>
        /*
        <AuthProvider>
            <ShiftProvider>
                <OfflineProvider>
                    <BrowserRouter>
                         <OfflineBanner />
                        <AppRoutes />
                    </BrowserRouter>
                </OfflineProvider>
            </ShiftProvider>
        </AuthProvider>
        */
    );
}

export default App;
