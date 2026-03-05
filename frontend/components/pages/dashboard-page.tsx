"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";
import { partyApi } from "@/lib/api";
import type { Party } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import PartyView from "./party-view";

export default function DashboardPage() {
    const { user, logout } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const [parties, setParties] = useState<Party[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedParty, setSelectedParty] = useState<string | null>(null);

    // Create party dialog
    const [createOpen, setCreateOpen] = useState(false);
    const [createName, setCreateName] = useState("");
    const [useGold, setUseGold] = useState(true);
    const [useElectrum, setUseElectrum] = useState(false);
    const [usePlatinum, setUsePlatinum] = useState(false);

    // Join party dialog
    const [joinOpen, setJoinOpen] = useState(false);
    const [joinCode, setJoinCode] = useState("");
    const [charName, setCharName] = useState("");
    const [charClass, setCharClass] = useState("");

    useEffect(() => {
        loadParties();
    }, []);

    const loadParties = async () => {
        try {
            const data = await partyApi.list();
            setParties(data);
        } catch {
            toast.error("Failed to load parties");
        } finally {
            setLoading(false);
        }
    };

    const handleCreateParty = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const party = await partyApi.create(createName, useGold, useElectrum, usePlatinum);
            toast.success(`Party "${party.name}" created! Code: ${party.code}`);
            setCreateOpen(false);
            setCreateName("");
            loadParties();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to create party";
            toast.error(message);
        }
    };

    const handleJoinParty = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await partyApi.join(joinCode.toUpperCase(), charName, charClass);
            toast.success("You have joined the party!");
            setJoinOpen(false);
            setJoinCode("");
            setCharName("");
            setCharClass("");
            loadParties();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to join party";
            toast.error(message);
        }
    };

    // If a party is selected, show its view
    if (selectedParty) {
        return (
            <PartyView
                partyCode={selectedParty}
                onBack={() => {
                    setSelectedParty(null);
                    loadParties();
                }}
            />
        );
    }

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="border-b border-border/40 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">⚔️</span>
                        <h1 className="text-xl font-bold text-dnd-red glow-red">D&D Currency</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={toggleTheme}
                            className="text-sm px-2 py-1 rounded-md bg-secondary/40 hover:bg-secondary/60 transition-colors"
                            title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
                        >
                            {theme === "dark" ? "☀️" : "🌙"}
                        </button>
                        <span className="text-sm text-muted-foreground">
                            {user?.username}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={logout}
                            className="text-muted-foreground hover:text-foreground"
                        >
                            Logout
                        </Button>
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
                {/* LAN Share URL */}
                <ShareUrlBanner />

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-3 mb-8">
                    <Dialog open={createOpen} onOpenChange={setCreateOpen}>
                        <DialogTrigger asChild>
                            <Button className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 h-12 text-base font-semibold">
                                ⚔️ Create Party
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="card-medieval border-border/40 sm:max-w-md">
                            <DialogHeader>
                                <DialogTitle className="text-gold text-xl">Forge a New Party</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleCreateParty} className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Party Name</Label>
                                    <Input
                                        placeholder="The Dragon Slayers"
                                        value={createName}
                                        onChange={(e) => setCreateName(e.target.value)}
                                        className="bg-secondary/30"
                                        required
                                    />
                                </div>
                                <Separator className="bg-border/30" />
                                <div className="space-y-2">
                                    <Label className="text-sm text-muted-foreground">Enabled Coins</Label>
                                    <div className="flex flex-wrap gap-2">
                                        <CoinToggle label="🪙 Gold" checked={useGold} onChange={setUseGold} />
                                        <CoinToggle label="⚡ Electrum" checked={useElectrum} onChange={setUseElectrum} />
                                        <CoinToggle label="💎 Platinum" checked={usePlatinum} onChange={setUsePlatinum} />
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">Silver & Copper are always enabled</p>
                                </div>
                                <Button type="submit" className="w-full bg-primary text-primary-foreground">
                                    Create Party
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>

                    <Dialog open={joinOpen} onOpenChange={setJoinOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="flex-1 h-12 text-base font-semibold border-border/40 hover:border-gold/50 hover:text-gold">
                                🏰 Join Party
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="card-medieval border-border/40 sm:max-w-md">
                            <DialogHeader>
                                <DialogTitle className="text-gold text-xl">Join an Adventure</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleJoinParty} className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Party Code</Label>
                                    <Input
                                        placeholder="A4F2"
                                        value={joinCode}
                                        onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                                        className="bg-secondary/30 text-center text-2xl tracking-[0.3em] font-mono uppercase"
                                        maxLength={4}
                                        required
                                    />
                                </div>
                                <Separator className="bg-border/30" />
                                <div className="space-y-2">
                                    <Label>Character Name</Label>
                                    <Input
                                        placeholder="Gandalf the Grey"
                                        value={charName}
                                        onChange={(e) => setCharName(e.target.value)}
                                        className="bg-secondary/30"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Character Class</Label>
                                    <Input
                                        placeholder="Wizard"
                                        value={charClass}
                                        onChange={(e) => setCharClass(e.target.value)}
                                        className="bg-secondary/30"
                                        required
                                    />
                                </div>
                                <Button type="submit" className="w-full bg-primary text-primary-foreground">
                                    Join Party
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Party List */}
                <h2 className="text-2xl font-bold text-dnd-red mb-4">Your Parties</h2>

                {loading ? (
                    <div className="text-center py-12 text-muted-foreground">Loading...</div>
                ) : parties.length === 0 ? (
                    <Card className="card-medieval">
                        <CardContent className="py-12 text-center">
                            <p className="text-4xl mb-4">🏰</p>
                            <p className="text-lg text-muted-foreground">No parties yet</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                Create a new party as DM or join one with a code
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 sm:grid-cols-2">
                        {parties.map((party) => (
                            <Card
                                key={party.id}
                                className="card-medieval cursor-pointer group"
                                onClick={() => setSelectedParty(party.code)}
                            >
                                <CardHeader className="pb-2">
                                    <div className="flex items-start justify-between">
                                        <CardTitle className="text-lg group-hover:text-dnd-red transition-colors">
                                            {party.name}
                                        </CardTitle>
                                        <Badge
                                            variant={party.is_active ? "default" : "secondary"}
                                            className={party.is_active
                                                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                                                : "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30"
                                            }
                                        >
                                            {party.is_active ? "Active" : "Archived"}
                                        </Badge>
                                    </div>
                                    <CardDescription className="font-mono tracking-wider text-muted-foreground">
                                        Code: {party.code}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        {party.dm_id === user?.id && (
                                            <Badge variant="outline" className="text-dnd-red border-dnd-red/30 text-xs">
                                                ⚔️ DM
                                            </Badge>
                                        )}
                                        <span>
                                            Coins: {party.use_platinum && "💎 "}{party.use_gold && "🪙 "}{party.use_electrum && "⚡ "}🥈 🟤
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

function CoinToggle({
    label,
    checked,
    onChange,
}: {
    label: string;
    checked: boolean;
    onChange: (v: boolean) => void;
}) {
    return (
        <button
            type="button"
            onClick={() => onChange(!checked)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${checked
                ? "bg-primary/20 text-gold border border-gold/30"
                : "bg-secondary/30 text-muted-foreground border border-transparent hover:border-border/50"
                }`}
        >
            {label}
        </button>
    );
}

function ShareUrlBanner() {
    const [copied, setCopied] = useState(false);
    const [lanUrl, setLanUrl] = useState("");

    useEffect(() => {
        // Fetch the actual LAN URL from the backend
        const fetchLanUrl = async () => {
            try {
                const res = await fetch(`http://${window.location.hostname}:8000/api/network/lan-url`, {
                    credentials: "include",
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.lan_url) {
                        setLanUrl(data.lan_url);
                        return;
                    }
                }
            } catch {
                // Backend not reachable — fall back
            }
            // Fallback: use current origin (better than nothing)
            setLanUrl(window.location.origin);
        };
        fetchLanUrl();
    }, []);

    if (!lanUrl) return null;

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(lanUrl);
        } catch {
            const input = document.createElement("input");
            input.value = lanUrl;
            document.body.appendChild(input);
            input.select();
            document.execCommand("copy");
            document.body.removeChild(input);
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const isLocalhost = lanUrl.includes("localhost") || lanUrl.includes("127.0.0.1");

    return (
        <div className="mb-6 flex items-center gap-3 rounded-lg bg-secondary/20 border border-border/30 px-4 py-3">
            <span className="text-sm text-muted-foreground shrink-0">📡 Share:</span>
            <code className={`text-sm font-mono truncate flex-1 ${isLocalhost ? "text-muted-foreground" : "text-gold"}`}>
                {lanUrl}
            </code>
            <button
                onClick={handleCopy}
                className="shrink-0 px-3 py-1 rounded-md text-xs font-medium bg-primary/20 text-gold border border-gold/30 hover:bg-primary/30 transition-all"
            >
                {copied ? "✓ Copied!" : "Copy"}
            </button>
        </div>
    );
}
