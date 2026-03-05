"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";
import { partyApi, transferApi, transactionApi, jointPaymentApi } from "@/lib/api";
import type {
    PartyDetail,
    CharacterInParty,
    TransactionResponse,
    JointPaymentResponse,
    CoinType,
} from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CoinDisplay } from "@/components/coin-display";
import { CoinInput } from "@/components/coin-input";
import { usePartySSE } from "@/hooks/use-party-sse";
import { toast } from "sonner";

interface PartyViewProps {
    partyCode: string;
    onBack: () => void;
}

const TABS = ["party", "treasury", "splits", "history"] as const;
type TabId = (typeof TABS)[number];
const TAB_LABELS: Record<TabId, string> = {
    party: "🏰 Party",
    treasury: "🪙 Treasury",
    splits: "🤝 Splits",
    history: "📜 History",
};

export default function PartyView({ partyCode, onBack }: PartyViewProps) {
    const { user } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const [party, setParty] = useState<PartyDetail | null>(null);
    const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
    const [jointPayments, setJointPayments] = useState<JointPaymentResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<TabId>("party");

    // Swipe support
    const touchStartX = useRef(0);
    const contentRef = useRef<HTMLDivElement>(null);

    // Pull-to-refresh
    const [pullDistance, setPullDistance] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const pullStartY = useRef(0);
    const isPulling = useRef(false);

    const isDM = party?.dm_id === user?.id;
    const myCharacter = party?.characters.find(
        (c) => c.user_id === user?.id && c.is_active
    );

    const enabledCoins: CoinType[] = [
        ...(party?.use_platinum ? ["pp" as CoinType] : []),
        ...(party?.use_gold ? ["gp" as CoinType] : []),
        ...(party?.use_electrum ? ["ep" as CoinType] : []),
        "sp",
        "cp",
    ];

    const loadAll = useCallback(async () => {
        try {
            const [partyData, txData, jpData] = await Promise.all([
                partyApi.getDetail(partyCode),
                transactionApi.getHistory(partyCode, 1, 50),
                jointPaymentApi.list(partyCode),
            ]);
            setParty(partyData);
            setTransactions(txData.transactions);
            setJointPayments(jpData);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to load party";
            toast.error(message);
        } finally {
            setLoading(false);
        }
    }, [partyCode]);

    useEffect(() => { loadAll(); }, [loadAll]);

    // SSE real-time updates
    usePartySSE(partyCode, (event) => {
        if (["balance_update", "transaction_new", "joint_payment_update", "party_update"].includes(event)) {
            loadAll();
        }
    });

    // Swipe handling for tab navigation
    const handleTouchStart = (e: React.TouchEvent) => {
        touchStartX.current = e.touches[0].clientX;
        // Pull-to-refresh: track vertical start
        const scrollTop = contentRef.current?.scrollTop ?? 0;
        if (scrollTop <= 0) {
            pullStartY.current = e.touches[0].clientY;
            isPulling.current = true;
        }
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        if (!isPulling.current) return;
        const dy = e.touches[0].clientY - pullStartY.current;
        if (dy > 0 && !isRefreshing) {
            setPullDistance(Math.min(dy * 0.5, 80));
        }
    };

    const handleTouchEnd = (e: React.TouchEvent) => {
        // Horizontal swipe for tab navigation
        const diffX = touchStartX.current - e.changedTouches[0].clientX;
        if (Math.abs(diffX) > 60) {
            const idx = TABS.indexOf(activeTab);
            if (diffX > 0 && idx < TABS.length - 1) setActiveTab(TABS[idx + 1]);
            if (diffX < 0 && idx > 0) setActiveTab(TABS[idx - 1]);
        }

        // Pull-to-refresh
        if (isPulling.current && pullDistance > 50 && !isRefreshing) {
            setIsRefreshing(true);
            loadAll().finally(() => {
                setIsRefreshing(false);
                setPullDistance(0);
                toast.success("Refreshed! 🔄");
            });
        } else {
            setPullDistance(0);
        }
        isPulling.current = false;
    };

    if (loading || !party) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <p className="text-muted-foreground animate-fade-in">Loading...</p>
            </div>
        );
    }

    const pendingCount = jointPayments.filter((p) => {
        if (p.status !== "pending") return false;
        if (isDM) return true;
        if (!myCharacter) return false;
        if (p.creator_character_id === myCharacter.id) return true;
        return p.participants.some(
            (pt) => pt.character_id === myCharacter.id && !pt.has_accepted
        );
    }).length;

    return (
        <div className="min-h-screen flex flex-col pb-16">
            {/* Header */}
            <header className="border-b border-border/40 bg-card/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-lg mx-auto px-4 py-2.5 flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                        <button onClick={onBack} className="text-muted-foreground hover:text-foreground text-sm shrink-0">
                            ← Back
                        </button>
                        <h1 className="text-base font-bold text-dnd-red truncate">{party.name}</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={toggleTheme}
                            className="text-sm px-2 py-1 rounded-md bg-secondary/40 hover:bg-secondary/60 transition-colors"
                            title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
                        >
                            {theme === "dark" ? "☀️" : "🌙"}
                        </button>
                        <CopyBadge text={party.code} />
                    </div>
                </div>
            </header>

            {/* Tab Bar */}
            <div className="border-b border-border/30 bg-card/30 sticky top-[49px] z-30">
                <div className="max-w-lg mx-auto px-2 flex">
                    {TABS.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 py-3 text-xs sm:text-sm font-medium text-center transition-colors relative ${activeTab === tab
                                ? "text-dnd-red"
                                : "text-muted-foreground hover:text-foreground"
                                }`}
                        >
                            {TAB_LABELS[tab]}
                            {tab === "splits" && pendingCount > 0 && (
                                <span className="absolute -top-0.5 right-1 bg-dnd-red text-white text-[9px] rounded-full w-4 h-4 flex items-center justify-center">
                                    {pendingCount}
                                </span>
                            )}
                            {activeTab === tab && (
                                <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-dnd-red rounded-full" />
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Pull-to-refresh indicator */}
            {pullDistance > 0 && (
                <div
                    className="pull-indicator flex items-center justify-center text-muted-foreground text-xs"
                    style={{ height: pullDistance, opacity: Math.min(pullDistance / 50, 1) }}
                >
                    {pullDistance > 50 ? "Release to refresh ↻" : "Pull to refresh ↓"}
                </div>
            )}

            {/* Tab Content — swipeable */}
            <main
                ref={contentRef}
                className="flex-1 max-w-lg mx-auto w-full px-4 py-4 animate-fade-in overflow-auto"
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
            >
                {activeTab === "party" && (
                    <PartyTab
                        party={party}
                        isDM={isDM}
                        myCharacter={myCharacter}
                        partyCode={partyCode}
                        onRefresh={loadAll}
                        onBack={onBack}
                    />
                )}
                {activeTab === "treasury" && (
                    <TreasuryTab
                        party={party}
                        isDM={isDM}
                        myCharacter={myCharacter}
                        partyCode={partyCode}
                        enabledCoins={enabledCoins}
                        onRefresh={loadAll}
                    />
                )}
                {activeTab === "splits" && (
                    <SplitsTab
                        partyCode={partyCode}
                        isDM={isDM}
                        myCharacter={myCharacter}
                        characters={party.characters.filter((c) => c.is_active)}
                        enabledCoins={enabledCoins}
                        jointPayments={jointPayments}
                        onRefresh={loadAll}
                    />
                )}
                {activeTab === "history" && (
                    <HistoryTab transactions={transactions} />
                )}
            </main>

            {/* Fixed Bottom Balance Bar */}
            <div className="fixed bottom-0 left-0 right-0 border-t border-border/40 bg-card/90 backdrop-blur-sm z-50">
                <div className="max-w-lg mx-auto px-4 py-2.5 flex items-center justify-between">
                    {myCharacter ? (
                        <>
                            <div className="flex items-center gap-2 min-w-0">
                                <span className="text-xs text-muted-foreground shrink-0">{myCharacter.name}</span>
                                <Badge variant="outline" className="text-[10px] border-border/30 px-1.5 py-0 h-4">
                                    {myCharacter.character_class}
                                </Badge>
                            </div>
                            <CoinDisplay
                                coins={myCharacter.balance_display}
                                balanceCp={myCharacter.balance_cp}
                                enabledCoins={enabledCoins}
                                size="sm"
                                interactive
                                animated
                            />
                        </>
                    ) : isDM ? (
                        <div className="flex items-center gap-2 w-full justify-center">
                            <span className="text-gold text-sm font-semibold">👑 Dungeon Master</span>
                        </div>
                    ) : (
                        <span className="text-xs text-muted-foreground">Not in this party</span>
                    )}
                </div>
            </div>
        </div>
    );
}

/* ============================================
   Shared Components
   ============================================ */

function CopyBadge({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    const handleCopy = async () => {
        try { await navigator.clipboard.writeText(text); } catch {
            const i = document.createElement("input"); i.value = text;
            document.body.appendChild(i); i.select(); document.execCommand("copy");
            document.body.removeChild(i);
        }
        setCopied(true); setTimeout(() => setCopied(false), 1500);
    };
    return (
        <button
            onClick={handleCopy}
            className="px-2 py-1 rounded-md text-xs font-mono bg-secondary/40 text-gold border border-border/30 hover:border-gold/30 transition-all"
        >
            {copied ? "✓ Copied" : `Code: ${text}`}
        </button>
    );
}

/* ============================================
   D&D-Themed Empty State Icons (inline SVGs)
   ============================================ */

function EmptyState({ icon, message }: { icon: "shield" | "scroll" | "handshake" | "chest"; message: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground animate-fade-in">
            <div className="w-16 h-16 mb-3 opacity-40">
                {icon === "shield" && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                        <path d="M12 8v4M12 16h.01" />
                    </svg>
                )}
                {icon === "scroll" && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M8 21h12a2 2 0 002-2v-2H10v2a2 2 0 01-2 2zm0 0a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2v12" />
                        <path d="M12 7h6M12 11h6M12 15h2" />
                    </svg>
                )}
                {icon === "handshake" && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20.42 4.58a5.4 5.4 0 00-7.65 0l-.77.78-.77-.78a5.4 5.4 0 00-7.65 0C1.46 6.7 1.33 10.28 4 13l8 8 8-8c2.67-2.72 2.54-6.3.42-8.42z" />
                    </svg>
                )}
                {icon === "chest" && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="2" y="7" width="20" height="14" rx="2" />
                        <path d="M16 7V5a4 4 0 00-8 0v2" />
                        <circle cx="12" cy="15" r="2" />
                    </svg>
                )}
            </div>
            <p className="text-sm text-center max-w-48">{message}</p>
        </div>
    );
}

/* ============================================
   PARTY TAB
   ============================================ */

function PartyTab({
    party, isDM, myCharacter, partyCode, onRefresh, onBack,
}: {
    party: PartyDetail; isDM: boolean; myCharacter: CharacterInParty | undefined;
    partyCode: string; onRefresh: () => void; onBack: () => void;
}) {
    const otherMembers = party.characters.filter(
        (c) => c.is_active && c.id !== myCharacter?.id
    );

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-bold text-dnd-red">Party Members</h3>
            <div className="space-y-2">
                {otherMembers.map((char) => (
                    <div
                        key={char.id}
                        className="flex items-center justify-between py-2.5 px-3 rounded-lg bg-secondary/20 border border-border/20"
                    >
                        <div className="min-w-0">
                            <p className="font-medium text-sm truncate">{char.name}</p>
                            <p className="text-xs text-muted-foreground">{char.character_class}</p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            <CoinDisplay coins={char.balance_display} size="sm" />
                            {isDM && (
                                <button
                                    onClick={async () => {
                                        if (!confirm(`Kick ${char.name}?`)) return;
                                        try {
                                            await partyApi.kick(partyCode, char.id);
                                            toast.success(`${char.name} kicked`);
                                            onRefresh();
                                        } catch { toast.error("Failed"); }
                                    }}
                                    className="text-[10px] text-destructive hover:underline ml-1"
                                >
                                    Kick
                                </button>
                            )}
                        </div>
                    </div>
                ))}
                {otherMembers.length === 0 && (
                    <EmptyState icon="shield" message="No adventurers yet — share the party code!" />
                )}
            </div>

            {/* DM Settings */}
            {isDM && (
                <PartySettings partyCode={partyCode} party={party} onRefresh={onRefresh} onBack={onBack} />
            )}
        </div>
    );
}

/* ============================================
   TREASURY TAB — Unified Transfer Card
   ============================================ */

type TransferTarget = "member" | "npc" | "self";

function TreasuryTab({
    party, isDM, myCharacter, partyCode, enabledCoins, onRefresh,
}: {
    party: PartyDetail; isDM: boolean; myCharacter: CharacterInParty | undefined;
    partyCode: string; enabledCoins: CoinType[]; onRefresh: () => void;
}) {
    return (
        <div className="space-y-5">
            {/* Player unified transfer */}
            {myCharacter && (
                <UnifiedTransferCard
                    partyCode={partyCode}
                    myCharacter={myCharacter}
                    otherCharacters={party.characters.filter((c) => c.is_active && c.id !== myCharacter.id)}
                    enabledCoins={enabledCoins}
                    onDone={onRefresh}
                />
            )}

            {/* DM Controls */}
            {isDM && (
                <DMControls
                    partyCode={partyCode}
                    characters={party.characters.filter((c) => c.is_active)}
                    enabledCoins={enabledCoins}
                    onDone={onRefresh}
                />
            )}
        </div>
    );
}

function UnifiedTransferCard({
    partyCode, myCharacter, otherCharacters, enabledCoins, onDone,
}: {
    partyCode: string; myCharacter: CharacterInParty;
    otherCharacters: CharacterInParty[]; enabledCoins: CoinType[]; onDone: () => void;
}) {
    const [target, setTarget] = useState<TransferTarget>("member");
    const [receiverId, setReceiverId] = useState<number | null>(null);
    const [amount, setAmount] = useState<Record<string, number>>({});
    const [reason, setReason] = useState("");
    const [sending, setSending] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (Object.keys(amount).length === 0) return toast.error("Enter an amount");

        if (target === "member" && !receiverId) return toast.error("Select a recipient");
        if (target === "npc" && !reason.trim()) return toast.error("Enter what you're buying");

        setSending(true);
        try {
            if (target === "member") {
                await transferApi.p2p(partyCode, receiverId!, amount, reason || undefined);
                toast.success("Transfer complete! 🪙");
            } else if (target === "npc") {
                await transferApi.spend(partyCode, amount, reason);
                toast.success("Purchase complete! 🛒");
            } else {
                await transferApi.selfAdd(partyCode, amount, reason || undefined);
                toast.success("Funds added! 💰");
            }
            setReceiverId(null);
            setAmount({});
            setReason("");
            onDone();
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed";
            toast.error(msg);
        } finally {
            setSending(false);
        }
    };

    return (
        <Card className="card-medieval">
            <CardHeader className="pb-3">
                <CardTitle className="text-base text-gold">Move Coins</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Target selector */}
                    <div className="flex gap-1.5">
                        {([
                            ["member", "💱 Send"] as const,
                            ["npc", "🛒 NPC/Shop"] as const,
                            ["self", "➕ Add to self"] as const,
                        ]).map(([key, label]) => (
                            <button
                                key={key}
                                type="button"
                                onClick={() => { setTarget(key); setReceiverId(null); }}
                                className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${target === key
                                    ? "bg-primary/20 text-dnd-red border border-dnd-red/30"
                                    : "bg-secondary/30 text-muted-foreground border border-transparent"
                                    }`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>

                    {/* Recipient selector (send only) */}
                    {target === "member" && (
                        <div className="space-y-1.5">
                            <Label className="text-xs">To</Label>
                            <div className="flex flex-wrap gap-1.5">
                                {otherCharacters.map((c) => (
                                    <button
                                        key={c.id}
                                        type="button"
                                        onClick={() => setReceiverId(c.id)}
                                        className={`px-3 py-2 rounded-md text-xs transition-all ${receiverId === c.id
                                            ? "bg-primary/20 text-dnd-red border border-dnd-red/30"
                                            : "bg-secondary/30 text-muted-foreground border border-transparent"
                                            }`}
                                    >
                                        {c.name}
                                    </button>
                                ))}
                                {otherCharacters.length === 0 && (
                                    <p className="text-xs text-muted-foreground py-2">No other members</p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Amount */}
                    <div className="space-y-1.5">
                        <Label className="text-xs">Amount</Label>
                        <CoinInput enabledCoins={enabledCoins} value={amount} onChange={setAmount} />
                    </div>

                    {/* Reason */}
                    <div className="space-y-1.5">
                        <Label className="text-xs">
                            {target === "npc" ? "What are you buying? *" : "Reason (optional)"}
                        </Label>
                        <Input
                            placeholder={
                                target === "npc"
                                    ? "Potion of Healing..."
                                    : target === "self"
                                        ? "Found loot in a chest..."
                                        : "For that enchanted sword..."
                            }
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            className="bg-secondary/20 border-border/30 h-10 text-sm"
                            required={target === "npc"}
                        />
                    </div>

                    <Button
                        type="submit"
                        className="w-full h-11 bg-primary text-primary-foreground font-medium"
                        disabled={sending}
                    >
                        {sending
                            ? "Processing..."
                            : target === "member"
                                ? "💱 Send Coins"
                                : target === "npc"
                                    ? "🛒 Spend Coins"
                                    : "➕ Add Funds"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}

function DMControls({
    partyCode, characters, enabledCoins, onDone,
}: {
    partyCode: string; characters: CharacterInParty[];
    enabledCoins: CoinType[]; onDone: () => void;
}) {
    const [selectedChars, setSelectedChars] = useState<number[]>([]);
    const [amount, setAmount] = useState<Record<string, number>>({});
    const [reason, setReason] = useState("");
    const [isDeduction, setIsDeduction] = useState(false);
    const [mode, setMode] = useState<"loot" | "god">("loot");
    const [sending, setSending] = useState(false);

    const toggleChar = (id: number) =>
        setSelectedChars((p) => (p.includes(id) ? p.filter((c) => c !== id) : [...p, id]));

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (selectedChars.length === 0) return toast.error("Select characters");
        if (Object.keys(amount).length === 0) return toast.error("Enter an amount");
        setSending(true);
        try {
            if (mode === "loot") {
                await transferApi.loot(partyCode, selectedChars, amount, reason || undefined);
                toast.success("Loot distributed! 💰");
            } else {
                for (const id of selectedChars) {
                    await transferApi.godMode(partyCode, id, amount, isDeduction, reason || undefined);
                }
                toast.success(isDeduction ? "Funds deducted" : "Funds added");
            }
            setSelectedChars([]); setAmount({}); setReason(""); onDone();
        } catch (err: unknown) {
            toast.error(err instanceof Error ? err.message : "Failed");
        } finally { setSending(false); }
    };

    return (
        <Card className="card-medieval border-dnd-red/20">
            <CardHeader className="pb-3">
                <CardTitle className="text-base text-dnd-red">👑 DM Controls</CardTitle>
            </CardHeader>
            <CardContent>
                {/* Mode toggle */}
                <div className="flex gap-1.5 mb-4">
                    <button type="button" onClick={() => { setMode("loot"); setIsDeduction(false); }}
                        className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${mode === "loot" ? "bg-green-900/30 text-green-400 border border-green-700/50" : "bg-secondary/30 text-muted-foreground"}`}>
                        💰 Loot
                    </button>
                    <button type="button" onClick={() => setMode("god")}
                        className={`flex-1 py-2.5 rounded-md text-xs font-medium transition-all ${mode === "god" ? "bg-purple-900/30 text-purple-400 border border-purple-700/50" : "bg-secondary/30 text-muted-foreground"}`}>
                        ⚡ God Mode
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <Label className="text-xs">Characters</Label>
                        <div className="flex flex-wrap gap-1.5">
                            {characters.map((c) => (
                                <button key={c.id} type="button" onClick={() => toggleChar(c.id)}
                                    className={`px-3 py-2 rounded-md text-xs transition-all ${selectedChars.includes(c.id) ? "bg-primary/20 text-dnd-red border border-dnd-red/30" : "bg-secondary/30 text-muted-foreground border border-transparent"}`}>
                                    {c.name}
                                </button>
                            ))}
                            {mode === "loot" && (
                                <button type="button"
                                    onClick={() => setSelectedChars(selectedChars.length === characters.length ? [] : characters.map((c) => c.id))}
                                    className="px-3 py-2 rounded-md text-[10px] bg-secondary/20 text-muted-foreground">
                                    {selectedChars.length === characters.length ? "None" : "All"}
                                </button>
                            )}
                        </div>
                    </div>

                    {mode === "god" && (
                        <div className="flex gap-1.5">
                            <button type="button" onClick={() => setIsDeduction(false)}
                                className={`flex-1 py-2 rounded-md text-xs ${!isDeduction ? "bg-green-900/30 text-green-400 border border-green-700/50" : "bg-secondary/30 text-muted-foreground"}`}>
                                ➕ Add
                            </button>
                            <button type="button" onClick={() => setIsDeduction(true)}
                                className={`flex-1 py-2 rounded-md text-xs ${isDeduction ? "bg-red-900/30 text-red-400 border border-red-700/50" : "bg-secondary/30 text-muted-foreground"}`}>
                                ➖ Deduct
                            </button>
                        </div>
                    )}

                    <div className="space-y-1.5">
                        <Label className="text-xs">Amount {mode === "loot" && "(each)"}</Label>
                        <CoinInput enabledCoins={enabledCoins} value={amount} onChange={setAmount} />
                    </div>

                    <div className="space-y-1.5">
                        <Label className="text-xs">Reason (optional)</Label>
                        <Input placeholder={mode === "loot" ? "Dragon treasure..." : "Divine intervention..."}
                            value={reason} onChange={(e) => setReason(e.target.value)}
                            className="bg-secondary/20 border-border/30 h-10 text-sm" />
                    </div>

                    <Button type="submit" className={`w-full h-11 font-medium ${isDeduction ? "bg-destructive text-white" : "bg-primary text-primary-foreground"}`} disabled={sending}>
                        {sending ? "..." : mode === "loot" ? "💰 Distribute Loot" : isDeduction ? "➖ Deduct" : "➕ Add Funds"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}

/* ============================================
   SPLITS TAB
   ============================================ */

function SplitsTab({
    partyCode, isDM, myCharacter, characters, enabledCoins, jointPayments, onRefresh,
}: {
    partyCode: string; isDM: boolean; myCharacter: CharacterInParty | undefined;
    characters: CharacterInParty[]; enabledCoins: CoinType[];
    jointPayments: JointPaymentResponse[]; onRefresh: () => void;
}) {
    const [createOpen, setCreateOpen] = useState(false);
    const [selectedChars, setSelectedChars] = useState<number[]>([]);
    const [amount, setAmount] = useState<Record<string, number>>({});
    const [reason, setReason] = useState("");
    const [receiverId, setReceiverId] = useState<number | null>(null);
    const [payTarget, setPayTarget] = useState<"npc" | "member">("npc");

    const pending = jointPayments.filter((p) => p.status === "pending");
    const past = jointPayments.filter((p) => p.status !== "pending");

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (selectedChars.length === 0) return toast.error("Select participants");
        if (Object.keys(amount).length === 0) return toast.error("Enter an amount");
        if (payTarget === "member" && !receiverId) return toast.error("Select who receives the money");
        try {
            const rcvId = payTarget === "member" ? receiverId ?? undefined : undefined;
            if (isDM) {
                await jointPaymentApi.createDM(partyCode, selectedChars, amount, reason || undefined, rcvId);
            } else {
                await jointPaymentApi.create(partyCode, selectedChars, amount, reason || undefined, rcvId);
            }
            toast.success("Split created!");
            setCreateOpen(false); setSelectedChars([]); setAmount({}); setReason(""); setReceiverId(null);
            onRefresh();
        } catch (err: unknown) { toast.error(err instanceof Error ? err.message : "Failed"); }
    };

    const handleAction = async (id: number, action: "accept" | "reject" | "cancel") => {
        try {
            if (action === "accept") { await jointPaymentApi.accept(partyCode, id); toast.success("Accepted!"); }
            else if (action === "reject") { await jointPaymentApi.reject(partyCode, id); toast.success("Rejected"); }
            else { await jointPaymentApi.cancel(partyCode, id); toast.success("Cancelled"); }
            onRefresh();
        } catch (err: unknown) { toast.error(err instanceof Error ? err.message : "Failed"); }
    };

    // Characters who can be recipients (not in the selected participant list)
    const availableReceivers = characters.filter(
        (c) => !selectedChars.includes(c.id)
    );

    return (
        <div className="space-y-4">
            {/* Create button */}
            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
                <DialogTrigger asChild>
                    <Button className="w-full h-11 bg-primary text-primary-foreground font-medium">
                        🤝 Create New Split
                    </Button>
                </DialogTrigger>
                <DialogContent className="card-medieval border-border/40 sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-dnd-red">Create Split Payment</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCreate} className="space-y-4">
                        {/* Pay to NPC or Member toggle */}
                        <div className="flex gap-1.5">
                            <button type="button" onClick={() => { setPayTarget("npc"); setReceiverId(null); }}
                                className={`flex-1 py-2 rounded-md text-xs font-medium transition-all ${payTarget === "npc" ? "bg-primary/20 text-dnd-red border border-dnd-red/30" : "bg-secondary/30 text-muted-foreground border border-transparent"}`}>
                                🛒 Pay NPC
                            </button>
                            <button type="button" onClick={() => setPayTarget("member")}
                                className={`flex-1 py-2 rounded-md text-xs font-medium transition-all ${payTarget === "member" ? "bg-primary/20 text-dnd-red border border-dnd-red/30" : "bg-secondary/30 text-muted-foreground border border-transparent"}`}>
                                💱 Pay Member
                            </button>
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs">Participants (who pays)</Label>
                            <div className="flex flex-wrap gap-1.5">
                                {characters.map((c) => (
                                    <button key={c.id} type="button"
                                        onClick={() => {
                                            setSelectedChars((p) => p.includes(c.id) ? p.filter((x) => x !== c.id) : [...p, c.id]);
                                            // If this character was the receiver, clear them
                                            if (receiverId === c.id) setReceiverId(null);
                                        }}
                                        className={`px-3 py-2 rounded-md text-xs transition-all ${selectedChars.includes(c.id) ? "bg-primary/20 text-dnd-red border border-dnd-red/30" : "bg-secondary/30 text-muted-foreground"}`}>
                                        {c.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Receiver selector (pay member only) */}
                        {payTarget === "member" && (
                            <div className="space-y-1.5">
                                <Label className="text-xs">Recipient (who receives)</Label>
                                <div className="flex flex-wrap gap-1.5">
                                    {availableReceivers.map((c) => (
                                        <button key={c.id} type="button"
                                            onClick={() => setReceiverId(c.id)}
                                            className={`px-3 py-2 rounded-md text-xs transition-all ${receiverId === c.id ? "bg-green-900/30 text-green-400 border border-green-700/50" : "bg-secondary/30 text-muted-foreground border border-transparent"}`}>
                                            {c.name}
                                        </button>
                                    ))}
                                    {availableReceivers.length === 0 && (
                                        <p className="text-xs text-muted-foreground py-1">Select participants first</p>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="space-y-1.5">
                            <Label className="text-xs">Total (split equally)</Label>
                            <CoinInput enabledCoins={enabledCoins} value={amount} onChange={setAmount} />
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Reason</Label>
                            <Input placeholder={payTarget === "member" ? "Pooling money for..." : "Tavern bill..."} value={reason}
                                onChange={(e) => setReason(e.target.value)}
                                className="bg-secondary/20 border-border/30 h-10 text-sm" />
                        </div>
                        <Button type="submit" className="w-full h-11 bg-primary text-primary-foreground">
                            Create Split
                        </Button>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Pending */}
            {pending.length > 0 ? (
                <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Pending</h4>
                    {pending.map((p) => (
                        <SplitCard key={p.id} payment={p} myCharacter={myCharacter} isDM={isDM} onAction={handleAction} />
                    ))}
                </div>
            ) : (
                <EmptyState icon="handshake" message="No deals on the table — create a split to share costs!" />
            )}

            {/* Past */}
            {past.length > 0 && (
                <details className="text-sm">
                    <summary className="text-muted-foreground cursor-pointer hover:text-foreground text-xs">
                        {past.length} past split{past.length > 1 ? "s" : ""}
                    </summary>
                    <div className="space-y-2 mt-2">
                        {past.map((p) => (
                            <div key={p.id} className="flex items-center justify-between py-2 px-3 rounded-lg bg-secondary/10 border border-border/10 opacity-60">
                                <CoinDisplay coins={p.total_amount_display} size="sm" />
                                <Badge variant="outline" className={`text-[10px] ${p.status === "approved" ? "text-green-400 border-green-700/50" : p.status === "cancelled" ? "text-red-400 border-red-700/50" : "text-muted-foreground"}`}>
                                    {p.status}
                                </Badge>
                            </div>
                        ))}
                    </div>
                </details>
            )}
        </div>
    );
}

function SplitCard({
    payment, myCharacter, isDM, onAction,
}: {
    payment: JointPaymentResponse; myCharacter: CharacterInParty | undefined;
    isDM: boolean; onAction: (id: number, a: "accept" | "reject" | "cancel") => void;
}) {
    const isParticipant = myCharacter && payment.participants.some(
        (p) => p.character_id === myCharacter.id
    );
    const needsMyAction = myCharacter && payment.participants.some(
        (p) => p.character_id === myCharacter.id && !p.has_accepted
    );
    const canCancel = (payment.creator_is_dm && isDM) ||
        (myCharacter && payment.creator_character_id === myCharacter.id);

    return (
        <Card className={`card-medieval border-yellow-700/20 ${!isParticipant && !isDM ? "opacity-50" : ""}`}>
            <CardContent className="py-3 space-y-2">
                <div className="flex items-start justify-between">
                    <div>
                        <CoinDisplay coins={payment.total_amount_display} size="sm" />
                        {payment.reason && <p className="text-xs text-muted-foreground italic mt-0.5">{payment.reason}</p>}
                        <p className="text-[10px] text-muted-foreground mt-0.5">by {payment.creator_name || "DM"}</p>
                        {payment.receiver_name && (
                            <p className="text-[10px] text-green-400 mt-0.5">→ pays {payment.receiver_name}</p>
                        )}
                    </div>
                    <Badge className="bg-yellow-900/20 text-yellow-400 border-yellow-700/30 text-[10px]">Pending</Badge>
                </div>

                {/* Non-participant notice */}
                {!isParticipant && !isDM && (
                    <p className="text-[10px] text-muted-foreground italic">You are not part of this split</p>
                )}

                <div className="space-y-1">
                    {payment.participants.map((p) => (
                        <div key={p.character_id} className="flex items-center justify-between text-xs">
                            <span>{p.character_name}: <CoinDisplay coins={p.share_display} size="sm" /></span>
                            <span className={p.has_accepted ? "text-green-400" : "text-yellow-500"}>{p.has_accepted ? "✓" : "…"}</span>
                        </div>
                    ))}
                </div>

                {needsMyAction && (
                    <div className="flex gap-2">
                        <Button size="sm" className="flex-1 h-9 bg-green-900/30 text-green-400 hover:bg-green-900/50"
                            onClick={() => onAction(payment.id, "accept")}>✓ Accept</Button>
                        <Button size="sm" variant="outline" className="flex-1 h-9 text-red-400 border-red-700/50 hover:bg-red-900/30"
                            onClick={() => onAction(payment.id, "reject")}>✗ Reject</Button>
                    </div>
                )}
                {canCancel && (
                    <button onClick={() => onAction(payment.id, "cancel")}
                        className="w-full text-center text-[10px] text-muted-foreground hover:text-destructive py-1">
                        Cancel
                    </button>
                )}
            </CardContent>
        </Card>
    );
}

/* ============================================
   HISTORY TAB
   ============================================ */

function HistoryTab({ transactions }: { transactions: TransactionResponse[] }) {
    const labels: Record<string, { icon: string; label: string; color: string }> = {
        transfer: { icon: "💱", label: "Transfer", color: "text-blue-400" },
        dm_grant: { icon: "💰", label: "DM Loot", color: "text-green-400" },
        dm_deduct: { icon: "⚡", label: "DM Deduct", color: "text-red-400" },
        joint_payment: { icon: "🤝", label: "Split", color: "text-yellow-400" },
        spend: { icon: "🛒", label: "NPC Purchase", color: "text-copper" },
        self_add: { icon: "➕", label: "Self Add", color: "text-green-300" },
    };

    return (
        <ScrollArea className="h-[calc(100vh-200px)]">
            {transactions.length === 0 ? (
                <EmptyState icon="scroll" message="No tales to tell yet — make your first transaction!" />
            ) : (
                <div className="space-y-1">
                    {transactions.map((txn) => {
                        const info = labels[txn.transaction_type] || labels.transfer;
                        return (
                            <div key={txn.id} className="flex items-start justify-between py-2.5 px-3 rounded-lg hover:bg-secondary/10 transition-colors">
                                <div className="min-w-0 flex-1">
                                    <div className="flex items-center gap-1.5">
                                        <span className="text-xs">{info.icon}</span>
                                        <span className={`text-xs font-medium ${info.color}`}>{info.label}</span>
                                    </div>
                                    <p className="text-[11px] text-muted-foreground mt-0.5 truncate">
                                        {txn.sender_name && <span>{txn.sender_name}</span>}
                                        {txn.sender_name && txn.receiver_name && " → "}
                                        {txn.receiver_name && <span>{txn.receiver_name}</span>}
                                    </p>
                                    {txn.reason && <p className="text-[11px] text-muted-foreground italic truncate">{txn.reason}</p>}
                                </div>
                                <div className="text-right shrink-0 ml-3">
                                    <CoinDisplay coins={txn.amount_display} size="sm" />
                                    <p className="text-[10px] text-muted-foreground mt-0.5">
                                        {new Date(txn.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                    </p>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </ScrollArea>
    );
}

/* ============================================
   PARTY SETTINGS (DM only)
   ============================================ */

function PartySettings({
    partyCode, party, onRefresh, onBack,
}: {
    partyCode: string; party: PartyDetail; onRefresh: () => void; onBack: () => void;
}) {
    const [saving, setSaving] = useState(false);

    const toggleCoin = async (coin: "use_gold" | "use_electrum" | "use_platinum", val: boolean) => {
        setSaving(true);
        try {
            await partyApi.updateCoins(partyCode, { [coin]: val });
            toast.success("Updated!"); onRefresh();
        } catch { toast.error("Failed"); }
        finally { setSaving(false); }
    };

    return (
        <Card className="card-medieval border-dnd-red/20 mt-4">
            <CardHeader className="pb-3">
                <CardTitle className="text-base text-dnd-red">⚙️ Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="space-y-1.5">
                    <Label className="text-xs text-muted-foreground">Coins</Label>
                    <div className="flex flex-wrap gap-1.5">
                        {([["use_gold", party.use_gold, "🪙 Gold", "text-gold"] as const,
                        ["use_electrum", party.use_electrum, "⚡ Electrum", "text-electrum"] as const,
                        ["use_platinum", party.use_platinum, "💎 Platinum", "text-platinum"] as const,
                        ]).map(([key, on, label, color]) => (
                            <button key={key} disabled={saving} onClick={() => toggleCoin(key, !on)}
                                className={`px-3 py-2 rounded-md text-xs font-medium transition-all ${on ? `bg-primary/20 ${color} border border-current/30` : "bg-secondary/30 text-muted-foreground border border-transparent"}`}>
                                {label}
                            </button>
                        ))}
                    </div>
                    <p className="text-[10px] text-muted-foreground">Silver & Copper always on</p>
                </div>
                <Separator className="bg-border/20" />
                {party.is_active && (
                    <Button variant="outline" size="sm"
                        className="w-full text-destructive border-destructive/30 hover:bg-destructive/10 h-9 text-xs"
                        onClick={async () => {
                            if (!confirm("Archive this party?")) return;
                            try { await partyApi.archive(partyCode); toast.success("Archived"); onBack(); }
                            catch { toast.error("Failed"); }
                        }}>
                        🗄️ Archive Party
                    </Button>
                )}
            </CardContent>
        </Card>
    );
}
