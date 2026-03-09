"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { partyApi, getApiBase } from "@/lib/api";
import type { Party } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Swords, Castle, Radio, Check } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import PartyView from "./party-view";

export default function DashboardPage() {
    const { user, logout } = useAuth();
    const [parties, setParties] = useState<Party[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedParty, setSelectedParty] = useState<string | null>(null);

    // Create party dialog
    const [createOpen, setCreateOpen] = useState(false);
    const [createName, setCreateName] = useState("");

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

            // Check for party invite after loading parties
            if (typeof window !== "undefined") {
                const params = new URLSearchParams(window.location.search);
                const inviteCode = params.get('party');
                if (inviteCode) {
                    // Remove ?party= from URL cleanly without reloading
                    window.history.replaceState({}, '', '/');

                    // Are they already in this party?
                    const existingParty = data.find(p => p.code.toUpperCase() === inviteCode.toUpperCase());
                    if (existingParty) {
                        setSelectedParty(existingParty.code);
                        toast.success("Welcome back to the party!");
                    } else {
                        // Not in the party, open join dialog
                        setJoinCode(inviteCode.toUpperCase());
                        setJoinOpen(true);
                    }
                }
            }
        } catch {
            toast.error("Failed to load parties");
        } finally {
            setLoading(false);
        }
    };

    const handleCreateParty = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const party = await partyApi.create(createName);
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
                <div className="w-full px-8 md:px-12 lg:px-16 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Swords className="text-dnd-red w-6 h-6" />
                        <h1 className="text-xl font-bold text-dnd-red glow-red">D&D Currency</h1>
                    </div>
                    <div className="flex items-center gap-3">
                        <ThemeToggle />
                        <span className="text-sm font-medium text-muted-foreground mr-2 hidden sm:inline-block">
                            {user?.username}
                        </span>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={logout}
                            className="bg-secondary/40 border-border/50 text-foreground hover:bg-secondary/60 h-9 px-3 font-semibold"
                        >
                            Logout
                        </Button>
                    </div>
                </div>
            </header>

            <main className="w-full px-8 md:px-12 lg:px-16 py-8 md:py-12 animate-fade-in">
                <div className="flex flex-col md:flex-row gap-8 lg:gap-12">

                    {/* Left Column: Actions & Info */}
                    <div className="w-full md:w-80 lg:w-96 shrink-0 flex flex-col gap-6">
                        {/* LAN Share URL */}
                        <ShareUrlBanner />

                        {/* Actions */}
                        <div>
                            <h2 className="text-lg font-bold text-dnd-red mb-3 flex items-center gap-2">
                                <Swords className="w-4 h-4" /> Quick Actions
                            </h2>
                            <div className="flex flex-col sm:flex-row md:flex-col gap-3">
                                <Dialog open={createOpen} onOpenChange={setCreateOpen}>
                                    <DialogTrigger asChild>
                                        <Button className="flex-1 md:w-full bg-primary text-primary-foreground hover:bg-primary/90 h-12 text-base font-bold flex items-center justify-center gap-2">
                                            <Swords className="w-5 h-5" /> Create Party
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
                                            <p className="text-xs text-muted-foreground">
                                                Players and DM can configure their own coin visibility from inside each party.
                                            </p>
                                            <Button type="submit" className="w-full bg-primary text-primary-foreground font-bold h-12">
                                                Create Party
                                            </Button>
                                        </form>
                                    </DialogContent>
                                </Dialog>

                                <Dialog open={joinOpen} onOpenChange={setJoinOpen}>
                                    <DialogTrigger asChild>
                                        <Button variant="outline" className="flex-1 md:w-full h-12 text-base font-bold flex items-center justify-center gap-2 border-border/60 hover:border-gold/50 hover:text-gold transition-colors shadow-sm">
                                            <Castle className="w-5 h-5" /> Join Party
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
                                            <Button type="submit" className="w-full bg-primary text-primary-foreground font-bold h-12">
                                                Join Party
                                            </Button>
                                        </form>
                                    </DialogContent>
                                </Dialog>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Party List */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-2xl font-bold text-dnd-red flex items-center gap-2">
                                <Castle className="w-6 h-6" /> Your Parties
                            </h2>
                            <Badge variant="outline" className="text-xs bg-secondary/20 shadow-none border-border/40 text-muted-foreground font-medium">
                                {parties.length} Total
                            </Badge>
                        </div>

                        {loading ? (
                            <div className="text-center py-12 text-muted-foreground animate-pulse bg-secondary/5 rounded-lg border border-border/10">Consulting the ledgers...</div>
                        ) : parties.length === 0 ? (
                            <Card className="card-medieval bg-secondary/5 border-border/20 shadow-none">
                                <CardContent className="py-16 flex flex-col items-center justify-center">
                                    <Castle className="w-16 h-16 text-muted-foreground/30 mb-4" />
                                    <p className="text-lg text-foreground font-medium">No parties yet</p>
                                    <p className="text-sm text-muted-foreground mt-1 text-center max-w-xs">
                                        Create a new party to establish an economy, or join an existing adventure with an invite code.
                                    </p>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="grid gap-4 sm:grid-cols-2">
                                {parties.map((party) => (
                                    <Card
                                        key={party.id}
                                        className="card-medieval cursor-pointer group hover:-translate-y-1 transition-transform duration-200 border-border/40 shadow-sm"
                                        onClick={() => setSelectedParty(party.code)}
                                    >
                                        <CardHeader className="pb-3">
                                            <div className="flex items-start justify-between">
                                                <CardTitle className="text-lg group-hover:text-dnd-red transition-colors flex items-center gap-2">
                                                    {party.name}
                                                </CardTitle>
                                                <Badge
                                                    variant={party.is_active ? "default" : "secondary"}
                                                    className={party.is_active
                                                        ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 font-semibold shadow-none"
                                                        : "bg-secondary/30 text-muted-foreground font-medium shadow-none"}
                                                >
                                                    {party.is_active ? "Active" : "Archived"}
                                                </Badge>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="flex flex-col gap-3">
                                                <div className="flex items-center gap-2 text-sm">
                                                    <span className="font-mono font-bold text-primary bg-secondary/20 border border-border/30 px-1.5 py-0.5 rounded text-xs tracking-wider">
                                                        {party.code}
                                                    </span>
                                                    {party.dm_id === user?.id && (
                                                        <Badge variant="outline" className="text-dnd-red border-dnd-red/30 text-[10px] h-5 px-1.5 font-bold tracking-widest uppercase shadow-none">
                                                            DM
                                                        </Badge>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-1.5 opacity-80">
                                                    {party.use_platinum && <div title="Platinum" className="w-3.5 h-3.5 rounded-full bg-platinum border border-foreground/20 shadow-sm" />}
                                                    {party.use_gold && <div title="Gold" className="w-3.5 h-3.5 rounded-full bg-gold border border-background shadow-sm" />}
                                                    {party.use_electrum && <div title="Electrum" className="w-3.5 h-3.5 rounded-full bg-electrum border border-background shadow-sm" />}
                                                    <div title="Silver" className="w-3.5 h-3.5 rounded-full bg-silver-coin border border-background shadow-sm" />
                                                    <div title="Copper" className="w-3.5 h-3.5 rounded-full bg-copper border border-background shadow-sm" />
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

function ShareUrlBanner() {
    const [copied, setCopied] = useState(false);
    const [lanUrl, setLanUrl] = useState("");
    const [shareWarning, setShareWarning] = useState<string | null>(null);

    useEffect(() => {
        // Fetch the actual LAN URL from the backend
        const fetchLanUrl = async () => {
            try {
                const res = await fetch(`${getApiBase()}/api/network/lan-url`, {
                    credentials: "include",
                });
                if (res.ok) {
                    const data = await res.json() as {
                        lan_url?: string | null;
                        warnings?: string[];
                    };
                    if (data.lan_url) {
                        setLanUrl(data.lan_url);
                        if (data.warnings?.length) {
                            setShareWarning(data.warnings[0]);
                        }
                        return;
                    }
                    if (data.warnings?.length) {
                        setShareWarning(data.warnings[0]);
                    }
                }
            } catch {
                // Backend not reachable — fall back
            }
            // Fallback: use current origin (better than nothing)
            setLanUrl(window.location.origin);
            if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
                setShareWarning("This link is local-only. Players need your LAN IP or a tunnel URL.");
            }
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
        <div className="mb-6 rounded-lg bg-secondary/20 border border-border/30 px-4 py-3 shadow-sm">
            <div className="flex items-center gap-3">
                <Radio className="w-4 h-4 text-muted-foreground shrink-0" />
                <span className="text-sm font-semibold text-muted-foreground shrink-0 hidden sm:inline">Share URL:</span>
                <code className={`text-sm font-mono truncate flex-1 ${isLocalhost ? "text-muted-foreground" : "text-gold glow-gold"}`}>
                    {lanUrl}
                </code>
                <button
                    onClick={handleCopy}
                    className="cursor-pointer shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold bg-primary/20 text-gold border border-gold/30 hover:bg-primary/30 transition-all uppercase tracking-wide"
                >
                    {copied ? <Check className="w-3 h-3" /> : null}
                    {copied ? "Copied" : "Copy"}
                </button>
            </div>

            {(shareWarning || isLocalhost) && (
                <p className="mt-2 text-xs text-amber-300">
                    {shareWarning || "Players cannot use localhost from other devices."} If this Wi-Fi blocks device-to-device traffic, use a tunnel like ngrok.
                </p>
            )}
        </div>
    );
}
