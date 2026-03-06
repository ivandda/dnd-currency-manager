"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "dark" | "light";

interface ThemeContextValue {
    theme: Theme;
    toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
    theme: "dark",
    toggleTheme: () => { },
});

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<Theme>("dark");

    useEffect(() => {
        // Read persisted theme on mount
        const stored = localStorage.getItem("theme") as Theme | null;
        if (stored === "light" || stored === "dark") {
            // eslint-disable-next-line react-hooks/exhaustive-deps
            setTheme(stored);
            if (stored === "light") {
                document.documentElement.classList.remove("dark");
                document.documentElement.classList.add("light");
            } else {
                document.documentElement.classList.remove("light");
                document.documentElement.classList.add("dark");
            }
        }
    }, []);

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        localStorage.setItem("theme", next);
        if (next === "light") {
            document.documentElement.classList.remove("dark");
            document.documentElement.classList.add("light");
        } else {
            document.documentElement.classList.remove("light");
            document.documentElement.classList.add("dark");
        }
    };

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    return useContext(ThemeContext);
}
