"use client";

import { useTheme } from "@/lib/theme-context";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="rounded-full w-10 h-10 bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary transition-colors"
            title="Toggle theme"
        >
            {theme === "dark" ? (
                <Sun className="h-5 w-5" />
            ) : (
                <Moon className="h-5 w-5" />
            )}
            <span className="sr-only">Toggle theme</span>
        </Button>
    );
}
