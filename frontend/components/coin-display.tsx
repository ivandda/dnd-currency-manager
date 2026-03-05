"use client";

import { COIN_COLORS, COIN_LABELS, type CoinType } from "@/lib/types";

interface CoinDisplayProps {
    coins: Record<string, number>;
    size?: "sm" | "md" | "lg";
    className?: string;
}

const COIN_ICONS: Record<CoinType, string> = {
    pp: "💎",
    gp: "🪙",
    ep: "⚡",
    sp: "🥈",
    cp: "🟤",
};

const SIZE_CLASSES = {
    sm: "text-sm gap-1.5",
    md: "text-base gap-2",
    lg: "text-lg gap-3",
};

export function CoinDisplay({ coins, size = "md", className = "" }: CoinDisplayProps) {
    const entries = Object.entries(coins).filter(
        ([key]) => key in COIN_LABELS
    ) as [CoinType, number][];

    if (entries.length === 0) {
        return <span className="text-muted-foreground">0 CP</span>;
    }

    return (
        <span className={`inline-flex items-center flex-wrap ${SIZE_CLASSES[size]} ${className}`}>
            {entries.map(([coin, amount]) => (
                <span key={coin} className={`inline-flex items-center gap-0.5 font-semibold ${COIN_COLORS[coin]}`}>
                    <span className="text-xs">{COIN_ICONS[coin]}</span>
                    {amount}
                    <span className="text-xs opacity-70 uppercase">{coin}</span>
                </span>
            ))}
        </span>
    );
}
