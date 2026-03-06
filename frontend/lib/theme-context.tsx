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
        const stored = localStorage.getItem("theme");
        if (stored === "light" || stored === "dark") {
            const t = stored as Theme;
            setTheme(t);
            if (t === "light") {
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
        
        const isLight = next === "light";
        document.documentElement.classList.toggle("dark", !isLight);
        document.documentElement.classList.toggle("light", isLight);
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
