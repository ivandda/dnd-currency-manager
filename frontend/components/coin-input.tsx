"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { CoinType } from "@/lib/types";

interface CoinInputProps {
    enabledCoins: CoinType[];
    value: Record<string, number>;
    onChange: (values: Record<string, number>) => void;
    className?: string;
}

const COIN_INFO: Record<CoinType, { label: string; color: string; icon: React.ReactNode }> = {
    pp: { label: "Platinum", color: "text-platinum", icon: <div title="Platinum" className="w-3 h-3 shrink-0 rounded-full bg-platinum border border-foreground/20 shadow-sm" /> },
    gp: { label: "Gold", color: "text-gold", icon: <div title="Gold" className="w-3 h-3 shrink-0 rounded-full bg-gold border border-background shadow-sm" /> },
    ep: { label: "Electrum", color: "text-electrum", icon: <div title="Electrum" className="w-3 h-3 shrink-0 rounded-full bg-electrum border border-background shadow-sm" /> },
    sp: { label: "Silver", color: "text-silver-coin", icon: <div title="Silver" className="w-3 h-3 shrink-0 rounded-full bg-silver-coin border border-background shadow-sm" /> },
    cp: { label: "Copper", color: "text-copper", icon: <div title="Copper" className="w-3 h-3 shrink-0 rounded-full bg-copper border border-background shadow-sm" /> },
};

export function CoinInput({ enabledCoins, value, onChange, className = "" }: CoinInputProps) {
    const handleChange = (coin: CoinType, rawValue: string) => {
        const num = parseInt(rawValue) || 0;
        const newValues = { ...value, [coin]: num };

        // Remove zero values
        Object.keys(newValues).forEach((key) => {
            if (newValues[key] === 0) delete newValues[key];
        });

        onChange(newValues);
    };

    const coins: CoinType[] = [
        ...(enabledCoins.includes("pp") ? ["pp" as CoinType] : []),
        ...(enabledCoins.includes("gp") ? ["gp" as CoinType] : []),
        ...(enabledCoins.includes("ep") ? ["ep" as CoinType] : []),
        "sp",
        "cp",
    ];

    return (
        <div className={`grid grid-cols-2 sm:grid-cols-3 gap-3 ${className}`}>
            {coins.map((coin) => {
                const info = COIN_INFO[coin];
                return (
                    <div key={coin} className="space-y-1">
                        <Label className={`text-xs ${info.color} flex items-center gap-1`}>
                            <span>{info.icon}</span> {info.label}
                        </Label>
                        <Input
                            type="number"
                            min={0}
                            placeholder="0"
                            value={value[coin] || ""}
                            onChange={(e) => handleChange(coin, e.target.value)}
                            className="bg-secondary/50 border-border/50 h-9"
                        />
                    </div>
                );
            })}
        </div>
    );
}
