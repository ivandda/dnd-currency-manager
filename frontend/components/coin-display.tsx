"use client";

import { useState } from "react";
import { COIN_COLORS, COIN_LABELS, type CoinType } from "@/lib/types";
import { AnimatedNumber } from "@/components/animated-number";

interface CoinDisplayProps {
    coins: Record<string, number>;
    /** Total balance in copper pieces — needed for currency conversion toggle */
    balanceCp?: number;
    /** Which coins are enabled for this party */
    enabledCoins?: CoinType[];
    size?: "sm" | "md" | "lg";
    /** When true, coin icons become clickable for currency conversion */
    interactive?: boolean;
    /** When true, values animate on change */
    animated?: boolean;
    className?: string;
}

const COIN_ICONS: Record<CoinType, string> = {
    pp: "💎",
    gp: "🪙",
    ep: "⚡",
    sp: "🥈",
    cp: "🟤",
};

/** How many copper pieces each coin is worth */
const CP_VALUES: Record<CoinType, number> = {
    pp: 1000,
    gp: 100,
    ep: 50,
    sp: 10,
    cp: 1,
};

const SIZE_CLASSES = {
    sm: "text-sm gap-1.5",
    md: "text-base gap-2",
    lg: "text-lg gap-3",
};

/**
 * Convert a total copper balance into a breakdown prioritizing a specific coin.
 * The target coin gets filled first, then the remainder trickles down to smaller coins.
 */
function convertToTargetCoin(
    totalCp: number,
    targetCoin: CoinType,
    enabledCoins: CoinType[]
): Record<string, number> {
    const result: Record<string, number> = {};
    let remaining = totalCp;

    // Build ordered coin list: target first, then the rest in descending value
    const ordered = [targetCoin, ...enabledCoins.filter((c) => c !== targetCoin)];

    for (const coin of ordered) {
        if (remaining <= 0) break;
        const value = CP_VALUES[coin];
        const count = Math.floor(remaining / value);
        if (count > 0) {
            result[coin] = count;
            remaining -= count * value;
        }
    }

    // If any remainder (shouldn't happen since cp=1, but be safe)
    if (remaining > 0) {
        result["cp"] = (result["cp"] || 0) + remaining;
    }

    return result;
}

export function CoinDisplay({
    coins,
    balanceCp,
    enabledCoins,
    size = "md",
    interactive = false,
    animated = false,
    className = "",
}: CoinDisplayProps) {
    const [convertTarget, setConvertTarget] = useState<CoinType | null>(null);

    // Determine which coins to show
    let displayCoins = coins;
    if (interactive && convertTarget && balanceCp !== undefined && enabledCoins) {
        displayCoins = convertToTargetCoin(balanceCp, convertTarget, enabledCoins);
    }

    const entries = Object.entries(displayCoins).filter(
        ([key, value]) => key in COIN_LABELS && value > 0
    ) as [CoinType, number][];

    if (entries.length === 0) {
        return <span className="text-muted-foreground">0 CP</span>;
    }

    const handleCoinClick = (coin: CoinType) => {
        if (!interactive) return;
        // Toggle: click same coin again to reset to normal view
        setConvertTarget((prev) => (prev === coin ? null : coin));
    };

    return (
        <span className={`inline-flex items-center flex-wrap ${SIZE_CLASSES[size]} ${className}`}>
            {entries.map(([coin, amount]) => (
                <span
                    key={coin}
                    className={`inline-flex items-center gap-0.5 font-semibold ${COIN_COLORS[coin]} ${interactive ? "cursor-pointer hover:opacity-80 transition-opacity" : ""
                        } ${convertTarget === coin ? "underline underline-offset-2" : ""}`}
                    onClick={() => handleCoinClick(coin)}
                    role={interactive ? "button" : undefined}
                    tabIndex={interactive ? 0 : undefined}
                >
                    <span className="text-xs">{COIN_ICONS[coin]}</span>
                    {animated ? (
                        <AnimatedNumber value={amount} />
                    ) : (
                        amount
                    )}
                    <span className="text-xs opacity-70 uppercase">{coin}</span>
                </span>
            ))}
        </span>
    );
}
