import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import { authApi } from '../api/auth';

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>({
        id: 1,
        email: 'admin@example.com',
        full_name: 'Admin User',
        role: 'admin',
        is_active: true
    });
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        // Auto-login logic (already set in state)
        setIsLoading(false);
    }, []);

    const login = async (username: string, password: string) => {
        // No-op login
        setUser({
            id: 1,
            email: 'admin@example.com',
            full_name: 'Admin User',
            role: 'admin',
            is_active: true
        });
    };

    const logout = async () => {
        setUser(null);
        // Optional: Reset to auto-login if you want strict "always on" or just let them logout to a blank screen
        // For now, allow logout but they can just refresh to "login" again
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                login,
                logout,
                isAuthenticated: !!user,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
