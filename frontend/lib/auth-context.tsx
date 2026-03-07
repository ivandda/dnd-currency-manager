"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { authApi, userApi, setAccessToken } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchUser = useCallback(async () => {
        try {
            const u = await userApi.getMe();
            setUser(u);
        } catch {
            setUser(null);
            setAccessToken(null);
        }
    }, []);

    // On mount, try to refresh the token (cookie-based)
    useEffect(() => {
        const init = async () => {
            try {
                const data = await authApi.refresh();
                setAccessToken(data.access_token);
                await fetchUser();
            } catch {
                // No valid refresh token — user needs to log in
                setUser(null);
            } finally {
                setIsLoading(false);
            }
        };
        init();
    }, [fetchUser]);

    const login = async (username: string, password: string) => {
        const data = await authApi.login(username, password);
        setAccessToken(data.access_token);
        await fetchUser();
    };

    const register = async (username: string, password: string) => {
        const data = await authApi.register(username, password);
        setAccessToken(data.access_token);
        await fetchUser();
    };

    const logout = async () => {
        try {
            await authApi.logout();
        } catch {
            // Continue even if server-side logout fails
        }
        setAccessToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
    return ctx;
}
