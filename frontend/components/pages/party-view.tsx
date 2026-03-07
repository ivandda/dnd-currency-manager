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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { CoinDisplay } from "@/components/coin-display";
import { CoinInput } from "@/components/coin-input";
import { usePartySSE } from "@/hooks/use-party-sse";
import { toast } from "sonner";
import {
    Castle, CircleDollarSign, Handshake, Scroll, Shield, Check, Crown, ArrowLeft,
    Zap, Gem, ArrowUpRight, Store, PlusCircle, Copy, Archive, Settings, Plus, Minus, X, Sun, Moon
} from "lucide-react";

interface PartyViewProps {
    partyCode: string;
    onBack: () => void;
}

/** Simple hook for window width reactivity */
function useWindowWidth() {
    const [width, setWidth] = useState(typeof window !== "undefined" ? window.innerWidth : 1024);
    useEffect(() => {
        const handleResize = () => setWidth(window.innerWidth);
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);
    return width;
}

const TABS = ["party", "treasury", "splits", "history"] as const;
type TabId = (typeof TABS)[number];
const TAB_LABELS: Record<TabId, { text: string; icon: React.ElementType }> = {
    party: { text: "Party", icon: Castle },
    treasury: { text: "Treasury", icon: CircleDollarSign },
    splits: { text: "Splits", icon: Handshake },
    history: { text: "History", icon: Scroll },
};

export default function PartyView({ partyCode, onBack }: PartyViewProps) {
    const { user } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const width = useWindowWidth();
    const [party, setParty] = useState<PartyDetail | null>(null);
    const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
    const [jointPayments, setJointPayments] = useState<JointPaymentResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<TabId>("party");
    const swipeStartX = useRef<number | null>(null);
    const swipeStartY = useRef<number | null>(null);

    const isDM = party?.dm_id === user?.id;
    const myCharacter = party?.characters.find(
        (c) => c.user_id === user?.id && c.is_active
    );

    const enabledCoins: CoinType[] = [
        ...((party?.my_coin_settings?.use_platinum ?? party?.use_platinum) ? ["pp" as CoinType] : []),
        ...((party?.my_coin_settings?.use_gold ?? party?.use_gold) ? ["gp" as CoinType] : []),
        ...((party?.my_coin_settings?.use_electrum ?? party?.use_electrum) ? ["ep" as CoinType] : []),
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

    const pendingCount = jointPayments.filter((p) => p.status === "pending").length;

    const handleSwipeStart = (e: React.TouchEvent) => {
        if (width >= 768) return;
        const touch = e.touches[0];
        swipeStartX.current = touch.clientX;
        swipeStartY.current = touch.clientY;
    };

    const handleSwipeEnd = (e: React.TouchEvent) => {
        if (width >= 768) return;
        if (swipeStartX.current === null || swipeStartY.current === null) return;

        const touch = e.changedTouches[0];
        const dx = touch.clientX - swipeStartX.current;
        const dy = touch.clientY - swipeStartY.current;
        swipeStartX.current = null;
        swipeStartY.current = null;

        // Keep vertical scroll behavior intact.
        if (Math.abs(dy) > 60) return;
        if (Math.abs(dx) < 70) return;

        const currentIndex = TABS.indexOf(activeTab);
        if (dx < 0 && currentIndex < TABS.length - 1) {
            setActiveTab(TABS[currentIndex + 1]);
        } else if (dx > 0 && currentIndex > 0) {
            setActiveTab(TABS[currentIndex - 1]);
        }
    };

    if (loading && !party) {
        return (
            <div className="h-screen flex items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    <p className="text-gold font-medium animate-pulse">Consulting the Scrolls...</p>
                </div>
            </div>
        );
    }

    if (!party) return <div>Party not found</div>;

    return (
        <div className="h-[100dvh] flex flex-col bg-background text-foreground overflow-hidden overscroll-none">
            {/* Header */}
            <header className="border-b border-border/40 bg-card/80 backdrop-blur-sm shrink-0 z-50 flex flex-col">
                <div className="w-full px-6 md:px-10 lg:px-16 py-2.5 flex items-center justify-between gap-4">
                    <div className="flex items-center min-w-0 shrink">
                        <button onClick={onBack} className="text-muted-foreground hover:text-foreground text-sm shrink-0 flex items-center gap-1">
                            <ArrowLeft className="w-4 h-4" /> Back
                        </button>
                        <Separator orientation="vertical" className="h-5 mx-2 sm:mx-3 bg-border/40" />
                        <div className="flex flex-col min-w-0">
                            <h1 className="text-base sm:text-lg font-bold text-dnd-red truncate glow-red-sm leading-tight">
                                {party.name}
                            </h1>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-4 shrink-0">
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-full hover:bg-secondary/20 transition-colors"
                            aria-label="Toggle theme"
                        >
                            {theme === "dark" ? <Sun className="w-4 h-4 text-gold" /> : <Moon className="w-4 h-4 text-primary" />}
                        </button>
                    </div>
                </div>
            </header>

            {/* Desktop / Mobile Dual Layout */}
            <div
                className="flex-1 min-h-0 flex flex-col md:flex-row w-full overflow-hidden relative"
                onTouchStart={handleSwipeStart}
                onTouchEnd={handleSwipeEnd}
            >

                {/* --- MOBILE TAB BAR (Hidden on md+) --- */}
                <div className="md:hidden border-b border-border/30 bg-card/30 shrink-0 z-30">
                    <div className="w-full px-2 flex">
                        {TABS.map((tab) => {
                            const Icon = TAB_LABELS[tab].icon;
                            const isSelected = activeTab === tab;
                            return (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`flex-1 py-3 flex flex-col items-center gap-0.5 transition-all relative ${isSelected ? "text-dnd-red" : "text-muted-foreground"}`}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span className="text-[10px] font-medium uppercase tracking-tighter">{TAB_LABELS[tab].text}</span>
                                    {isSelected && <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-dnd-red rounded-t-full" />}
                                    {tab === "splits" && pendingCount > 0 && (
                                        <span className="absolute top-1 right-1/4 bg-dnd-red text-white text-[9px] rounded-full w-3.5 h-3.5 flex items-center justify-center border-2 border-background">
                                            {pendingCount}
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* --- LEFT SIDEBAR: PARTY INFO (Desktop persistent, Mobile activeTab only) --- */}
                <aside className={`${activeTab === "party" ? "flex" : "hidden"} md:flex flex-col flex-1 min-h-0 w-full md:w-80 lg:w-96 md:flex-none md:shrink-0 md:border-r border-border/30 bg-card/10 overflow-hidden relative`}>
                    <div className="flex-1 min-h-0 overflow-y-auto px-6 lg:px-8 py-4 md:py-6 pb-6 mt-1.5">
                        <PartyTab
                            party={party}
                            isDM={isDM}
                            myCharacter={myCharacter}
                            partyCode={partyCode}
                            enabledCoins={enabledCoins}
                            onRefresh={loadAll}
                            onBack={onBack}
                        />
                    </div>
                </aside>

                {/* --- MAIN CONTENT AREA (Tabs for Desktop, Conditional for Mobile) --- */}
                <main className={`flex-1 min-h-0 flex flex-col overflow-hidden bg-background ${activeTab === "party" ? "hidden md:flex" : "flex"}`}>
                    {/* Desktop Tab Bar (Excludes Party Tab) */}
                    <div className="hidden md:flex border-b border-border/30 bg-card/60 backdrop-blur-md shrink-0 z-30 justify-start">
                        <div className="w-full px-8 md:px-12 lg:px-16 flex">
                            {TABS.filter(t => t !== "party").map((tab) => {
                                const Icon = TAB_LABELS[tab].icon;
                                const isSelected = activeTab === tab || (activeTab === "party" && tab === "treasury"); // Fallback for desktop when state is 'party'
                                return (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`flex-1 overflow-hidden py-3.5 text-sm font-medium text-center transition-all relative ${isSelected
                                            ? "text-dnd-red"
                                            : "text-muted-foreground hover:text-foreground hover:bg-secondary/20"
                                            }`}
                                    >
                                        <div className="flex items-center justify-center gap-1.5">
                                            <Icon className="w-4 h-4" />
                                            <span>{TAB_LABELS[tab].text}</span>
                                        </div>
                                        {tab === "splits" && pendingCount > 0 && (
                                            <span className="absolute top-1/2 -translate-y-1/2 right-[10%] bg-dnd-red text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                                                {pendingCount}
                                            </span>
                                        )}
                                        {isSelected && (
                                            <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-dnd-red" />
                                        )}
                                    </button>
                                )
                            })}
                        </div>
                    </div>

                    {/* Scrollable Content Container */}
                    <div className="flex-1 min-h-0 overflow-y-auto w-full relative">
                        {/* Tab Content Wrapper */}
                        <div className="w-full px-8 md:px-12 lg:px-16 py-4 md:py-6 pb-6 animate-fade-in">
                            {(activeTab === "treasury" || (activeTab === "party" && width >= 768)) && (
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
                                    characters={party.characters.filter(c => c.is_active)}
                                    enabledCoins={enabledCoins}
                                    jointPayments={jointPayments}
                                    onRefresh={loadAll}
                                />
                            )}
                            {activeTab === "history" && (
                                <HistoryTab transactions={transactions} />
                            )}
                        </div>
                    </div>
                </main>
            </div>

            {/* Identity / Balance Footer */}
            <footer className="md:hidden bg-secondary/10 border-t border-border/20 shrink-0 z-50">
                <div className="w-full px-8 md:px-12 lg:px-16 py-3 flex items-center justify-between">
                    {myCharacter ? (
                        <>
                            <div className="flex items-center gap-3 min-w-0">
                                <span className="text-sm font-semibold text-foreground truncate">{myCharacter.name}</span>
                                <Badge variant="outline" className="text-[10px] border-border/30 px-1.5 py-0 h-4.5 bg-background/50 flex shrink-0">
                                    {myCharacter.character_class}
                                </Badge>
                            </div>
                            <div className="flex shrink-0 ml-2">
                                <CoinDisplay
                                    coins={myCharacter.balance_display}
                                    balanceCp={myCharacter.balance_cp}
                                    enabledCoins={enabledCoins}
                                    size="sm"
                                    interactive
                                    animated
                                />
                            </div>
                        </>
                    ) : isDM ? (
                        <div className="flex items-center gap-2 w-full justify-center">
                            <span className="text-gold text-sm font-semibold flex items-center gap-1.5 shrink-0"><Crown className="w-5 h-5" /> Dungeon Master</span>
                        </div>
                    ) : (
                        <div className="w-full text-center">
                            <span className="text-sm text-muted-foreground shrink-0">Observer</span>
                        </div>
                    )}
                </div>
            </footer>
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
            className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-mono bg-secondary/40 text-gold border border-border/30 hover:border-gold/30 transition-all font-semibold"
        >
            {copied ? <Check className="w-3 h-3 text-success" /> : <Copy className="w-3 h-3" />}
            {copied ? "Copied" : text}
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
    party, isDM, myCharacter, partyCode, enabledCoins, onRefresh, onBack,
}: {
    party: PartyDetail; isDM: boolean; myCharacter: CharacterInParty | undefined;
    partyCode: string; enabledCoins: CoinType[]; onRefresh: () => void; onBack: () => void;
}) {
    const activeCharacters = party.characters.filter(c => c.is_active);

    // Sort so myCharacter is first
    const sortedMembers = [...activeCharacters].sort((a, b) => {
        if (a.id === myCharacter?.id) return -1;
        if (b.id === myCharacter?.id) return 1;
        return a.name.localeCompare(b.name);
    });

    const joinUrl = typeof window !== "undefined" ? `${window.location.origin}/?party=${partyCode}` : "";

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-bold text-dnd-red pt-1 flex items-center gap-2 px-1">
                <Shield className="w-4 h-4" /> Party Members
            </h3>
            <div className="space-y-2">
                {sortedMembers.map((char) => (
                    <div
                        key={char.id}
                        className={`flex items-center justify-between py-2.5 px-3 rounded-lg border ${char.id === myCharacter?.id
                            ? "bg-primary/15 border-primary/50 shadow-sm"
                            : "bg-card/75 border-border/60"
                            }`}
                    >
                        <div className="min-w-0">
                            <p className="font-medium text-sm truncate flex items-center gap-2">
                                {char.name}
                                {char.id === myCharacter?.id && (
                                    <Badge variant="default" className="text-[10px] h-4 px-1.5 py-0 bg-primary/20 text-primary hover:bg-primary/30 border-none shadow-none font-bold">
                                        You
                                    </Badge>
                                )}
                            </p>
                            <p className="text-xs text-muted-foreground">{char.character_class}</p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            {char.balance_visible_to_viewer ? (
                                <CoinDisplay
                                    coins={char.balance_display}
                                    balanceCp={char.balance_cp}
                                    enabledCoins={enabledCoins}
                                    size="sm"
                                    interactive
                                    animated
                                />
                            ) : (
                                <span className="rounded border border-border/40 bg-secondary/30 px-2 py-1 text-xs font-medium text-muted-foreground">
                                    Hidden
                                </span>
                            )}
                            {isDM && char.id !== myCharacter?.id && (
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
                {sortedMembers.length === 0 && (
                    <EmptyState icon="shield" message="No adventurers yet — share the party code!" />
                )}
            </div>

            <Card className="card-medieval bg-secondary/10 border-border/30 shadow-none">
                <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                        <Castle className="w-4 h-4 text-primary" /> Invite Players
                    </CardTitle>
                    <CardDescription className="text-xs text-muted-foreground">
                        Share this code or link so players can join this party.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2.5">
                    <div className="flex items-center gap-2 rounded-md border border-border/50 bg-background/60 px-2 py-1.5">
                        <code className="flex-1 truncate font-mono text-xs tracking-[0.18em] text-primary">{partyCode}</code>
                        <CopyBadge text={partyCode} />
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-full border-dashed text-xs"
                        onClick={async () => {
                            try { await navigator.clipboard.writeText(joinUrl); toast.success("Link copied!"); }
                            catch { toast.error("Failed to copy link"); }
                        }}
                    >
                        <Copy className="mr-1.5 h-3.5 w-3.5 opacity-75" />
                        Copy Full Invite Link
                    </Button>
                </CardContent>
            </Card>

            <PartySettings
                partyCode={partyCode}
                party={party}
                isDM={isDM}
                myCharacter={myCharacter}
                onRefresh={onRefresh}
                onBack={onBack}
            />
        </div>
    );
}

/* ============================================
   TREASURY TAB — Unified Transfer Card
   ============================================ */

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
    partyCode, otherCharacters, enabledCoins, onDone,
}: {
    partyCode: string;
    otherCharacters: CharacterInParty[]; enabledCoins: CoinType[]; onDone: () => void;
}) {
    // "pay" covers sending to party member(s) and/or paying an NPC
    // "receive" covers finding gold / adding to your own balance
    const [actionType, setActionType] = useState<"pay" | "receive">("pay");
    const [selectedReceiverIds, setSelectedReceiverIds] = useState<number[]>([]);
    const [includeNpc, setIncludeNpc] = useState(false);
    const [amount, setAmount] = useState<Record<string, number>>({});
    const [reason, setReason] = useState("");
    const [sending, setSending] = useState(false);

    const toggleReceiver = (id: number) => {
        setSelectedReceiverIds(prev => 
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (Object.keys(amount).length === 0) return toast.error("Enter an amount");

        if (actionType === "pay" && selectedReceiverIds.length === 0 && !includeNpc) {
            return toast.error("Select at least one recipient");
        }
        if (includeNpc && !reason.trim()) return toast.error("Enter what you're buying");

        setSending(true);
        try {
            if (actionType === "pay") {
                if (selectedReceiverIds.length === 0 && includeNpc) {
                    // Just NPC
                    await transferApi.spend(partyCode, amount, reason);
                    toast.success("Purchase complete!");
                } else if (selectedReceiverIds.length === 1 && !includeNpc) {
                    // Single person P2P
                    await transferApi.p2p(partyCode, selectedReceiverIds[0], amount, reason || undefined);
                    toast.success("Transfer complete!");
                } else {
                    // Multiple recipients or Multi + NPC
                    await transferApi.distribute(partyCode, selectedReceiverIds, includeNpc, amount, reason || undefined);
                    toast.success("Distribution complete!");
                }
            } else {
                await transferApi.selfAdd(partyCode, amount, reason || undefined);
                toast.success("Funds added!");
            }
            setSelectedReceiverIds([]);
            setIncludeNpc(false);
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
                <CardTitle className="text-base text-gold flex items-center gap-2">
                    <CircleDollarSign className="w-5 h-5" /> Move Coins
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground mt-1">
                    Send money to party members, pay for items, or log new loot.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Action Type Segmented Control */}
                    <div className="space-y-1.5">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Action</Label>
                        <div className="flex gap-1.5 bg-secondary/10 p-1 rounded-lg border border-border/20">
                            <button
                                type="button"
                                onClick={() => { setActionType("pay"); setSelectedReceiverIds([]); setIncludeNpc(false); }}
                                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-sm font-medium transition-all ${actionType === "pay"
                                    ? "bg-card text-foreground shadow-sm border border-border/50"
                                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/30"
                                    }`}
                            >
                                <ArrowUpRight className="w-4 h-4" /> Pay / Send
                            </button>
                            <button
                                type="button"
                                onClick={() => { setActionType("receive"); setSelectedReceiverIds([]); setIncludeNpc(false); }}
                                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-sm font-medium transition-all ${actionType === "receive"
                                    ? "bg-card text-foreground shadow-sm border border-border/50"
                                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/30"
                                    }`}
                            >
                                <PlusCircle className="w-4 h-4" /> Add Funds
                            </button>
                        </div>
                    </div>

                    {/* Recipient Selector (Pay only) */}
                    {actionType === "pay" && (
                        <div className="space-y-2">
                            <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Recipient(s)</Label>
                            <div className="flex flex-wrap gap-1.5">
                                <button
                                    type="button"
                                    onClick={() => setIncludeNpc(!includeNpc)}
                                    className={`px-3 py-2 rounded-md text-xs transition-all border flex items-center gap-1.5 ${includeNpc
                                        ? "bg-primary/20 text-dnd-red border-dnd-red/30 shadow-sm"
                                        : "bg-secondary/20 text-muted-foreground border-transparent hover:border-border/50 hover:bg-secondary/40"
                                        }`}
                                >
                                    <Store className="w-3.5 h-3.5 opacity-70" />
                                    NPC / Shop
                                </button>
                                {otherCharacters.map((c) => (
                                    <button
                                        key={c.id}
                                        type="button"
                                        onClick={() => toggleReceiver(c.id)}
                                        className={`px-3 py-2 rounded-md text-xs transition-all border flex items-center gap-1.5 ${selectedReceiverIds.includes(c.id)
                                            ? "bg-primary/20 text-dnd-red border-dnd-red/30 shadow-sm"
                                            : "bg-secondary/20 text-muted-foreground border-transparent hover:border-border/50 hover:bg-secondary/40"
                                            }`}
                                    >
                                        <Shield className="w-3.5 h-3.5 opacity-70" />
                                        {c.name}
                                    </button>
                                ))}
                            </div>
                            { (selectedReceiverIds.length + (includeNpc ? 1 : 0)) > 1 && (
                                <p className="text-[10px] text-warning font-medium italic mt-1">
                                    Total amount will be split as evenly as possible among all {selectedReceiverIds.length + (includeNpc ? 1 : 0)} recipients. Any leftover copper that cannot be split exactly is assigned to a random recipient.
                                </p>
                            ) }
                        </div>
                    )}

                    {/* Amount */}
                    <div className="space-y-1.5">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            { (selectedReceiverIds.length + (includeNpc ? 1 : 0)) > 1 ? "Total Amount to Split" : "Amount" }
                        </Label>
                        <CoinInput enabledCoins={enabledCoins} value={amount} onChange={setAmount} />
                    </div>

                    {/* Reason */}
                    <div className="space-y-1.5">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            {includeNpc ? "What are you buying? *" : "Reason (optional)"}
                        </Label>
                        <Input
                            placeholder={
                                includeNpc
                                    ? "Potion of Healing..."
                                    : actionType === "receive"
                                        ? "Found loot in a chest..."
                                        : "For that enchanted sword..."
                            }
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            className="bg-secondary/20 border-border/30 h-10 text-sm"
                            required={includeNpc}
                        />
                    </div>

                    <Button
                        type="submit"
                        className="w-full h-12 bg-primary text-primary-foreground font-semibold flex items-center justify-center gap-2 text-base transition-transform hover:scale-[1.02] active:scale-100"
                        disabled={sending}
                    >
                        {sending
                            ? "Processing..."
                            : actionType === "pay"
                                ? (selectedReceiverIds.length + (includeNpc ? 1 : 0)) > 1
                                    ? <><ArrowUpRight className="w-5 h-5" /> Distribute Coins</>
                                    : includeNpc
                                        ? <><Store className="w-5 h-5" /> Spend Coins</>
                                        : <><ArrowUpRight className="w-5 h-5" /> Send Coins</>
                                : <><PlusCircle className="w-5 h-5" /> Add Funds</>}
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
    const [mode, setMode] = useState<"add" | "deduct">("add");
    const [sending, setSending] = useState(false);

    const toggleChar = (id: number) =>
        setSelectedChars((p) => (p.includes(id) ? p.filter((c) => c !== id) : [...p, id]));

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (selectedChars.length === 0) return toast.error("Select characters");
        if (Object.keys(amount).length === 0) return toast.error("Enter an amount");
        setSending(true);
        try {
            // Total amount is divided equally among selected characters.
            // Remainder (if any) is not distributed.
            if (mode === "add") {
                await transferApi.loot(partyCode, selectedChars, amount, reason || undefined, false);
                toast.success("Total funds added and divided equally!");
            } else {
                await transferApi.loot(partyCode, selectedChars, amount, reason || undefined, true);
                toast.success("Total funds deducted equally!");
            }
            setSelectedChars([]); setAmount({}); setReason(""); onDone();
        } catch (err: unknown) {
            toast.error(err instanceof Error ? err.message : "Failed");
        } finally { setSending(false); }
    };

    return (
        <Card className="card-medieval border-dnd-red/20 shadow-lg relative overflow-hidden">
            {/* Subtle background glow to distinguish DM panel */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-dnd-red/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
            <CardHeader className="pb-3 relative z-10">
                <CardTitle className="text-base text-dnd-red flex items-center gap-2">
                    <Crown className="w-5 h-5" /> Manage Coins
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground mt-1">
                    Directly oversee the economy. Changes log under your name.
                </CardDescription>
            </CardHeader>
            <CardContent className="relative z-10">
                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Action Segmented Control */}
                    <div className="space-y-1.5">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Action Type</Label>
                        <div className="flex gap-1.5 bg-secondary/10 p-1 rounded-lg border border-border/20 overflow-x-auto pb-2 sm:pb-1">
                            {([
                                ["add", "Add (Distribute)", Plus, "text-emerald-500"],
                                ["deduct", "Deduct", Minus, "text-red-500"]
                            ] as const).map(([key, label, Icon, colorClass]) => (
                                <button
                                    key={key}
                                    type="button"
                                    onClick={() => setMode(key)}
                                    className={`flex-1 min-w-[100px] flex items-center justify-center gap-1.5 py-2 px-2 rounded-md text-xs sm:text-sm font-medium transition-all ${mode === key
                                        ? "bg-card text-foreground shadow-sm border border-border/50"
                                        : "text-muted-foreground hover:text-foreground hover:bg-secondary/30"
                                        }`}
                                >
                                    <Icon className={`w-4 h-4 ${mode === key ? colorClass : ""}`} />
                                    {label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Characters */}
                    <div className="space-y-2">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Affect Characters</Label>
                        <div className="flex flex-wrap gap-1.5">
                            {characters.map((c) => (
                                <button key={c.id} type="button" onClick={() => toggleChar(c.id)}
                                    className={`px-3 py-2 rounded-md text-xs transition-all border ${selectedChars.includes(c.id) ? "bg-primary/20 text-dnd-red border-dnd-red/30 shadow-sm" : "bg-secondary/20 text-muted-foreground border-transparent hover:border-border/50"}`}>
                                    {c.name}
                                </button>
                            ))}
                            <button type="button"
                                onClick={() => setSelectedChars(selectedChars.length === characters.length ? [] : characters.map((c) => c.id))}
                                className="px-3 py-2 rounded-md text-[10px] bg-secondary/10 hover:bg-secondary/20 border border-border/30 text-muted-foreground font-medium uppercase min-w-[50px]">
                                {selectedChars.length === characters.length ? "None" : "All"}
                            </button>
                        </div>
                    </div>

                    {/* Amount */}
                    <div className="space-y-1.5">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Total Amount</Label>
                        <CoinInput enabledCoins={enabledCoins} value={amount} onChange={setAmount} />
                    </div>

                    {/* Reason */}
                    <div className="space-y-1.5">
                        <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reason (optional)</Label>
                        <Input placeholder={mode === "deduct" ? "Divine intervention..." : "Dragon treasure..."}
                            value={reason} onChange={(e) => setReason(e.target.value)}
                            className="bg-secondary/20 border-border/30 h-10 text-sm" />
                    </div>

                    <Button type="submit" className={`w-full h-12 font-semibold text-base transition-transform hover:scale-[1.02] active:scale-100 flex items-center justify-center gap-2 ${mode === "deduct" ? "bg-destructive text-white hover:bg-destructive/90" : "bg-primary text-primary-foreground hover:bg-primary/90"}`} disabled={sending}>
                        {sending ? "Processing..." : mode === "deduct" ? <><Minus className="w-5 h-5" /> Deduct Total Equally</> : <><Plus className="w-5 h-5" /> Add Total Equally</>}
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
            <p className="text-xs text-muted-foreground">
                Split shared costs across selected players. Everyone must approve before coins move.
            </p>
            {/* Create button */}
            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
                <DialogTrigger asChild>
                    <Button className="w-full h-11 bg-primary text-primary-foreground font-medium flex items-center justify-center gap-2">
                        <Handshake className="w-4 h-4" /> Create New Split
                    </Button>
                </DialogTrigger>
                <DialogContent className="card-medieval border-border/40 sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-dnd-red">Create Split Payment</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div className="flex gap-1.5">
                            <button type="button" onClick={() => { setPayTarget("npc"); setReceiverId(null); }}
                                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-medium transition-all border ${payTarget === "npc" ? "bg-primary/20 text-dnd-red border-dnd-red/30" : "bg-secondary/30 text-muted-foreground border-transparent"}`}>
                                <Store className="w-3.5 h-3.5" /> Pay NPC
                            </button>
                            <button type="button" onClick={() => setPayTarget("member")}
                                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-medium transition-all border ${payTarget === "member" ? "bg-primary/20 text-dnd-red border-dnd-red/30" : "bg-secondary/30 text-muted-foreground border-transparent"}`}>
                                <ArrowUpRight className="w-3.5 h-3.5" /> Pay Member
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
                                            className={`px-3 py-2 rounded-md text-xs transition-all ${receiverId === c.id ? "bg-success-soft text-success border border-success/40" : "bg-secondary/30 text-muted-foreground border border-transparent"}`}>
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
                                <Badge variant="outline" className={`text-[10px] ${p.status === "approved" ? "text-success border-success/40" : p.status === "cancelled" ? "text-danger border-danger/40" : "text-muted-foreground"}`}>
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
        <Card className={`card-medieval border-warning/25 ${!isParticipant && !isDM ? "opacity-50" : ""}`}>
            <CardContent className="py-3 space-y-2.5">
                <div className="flex items-start justify-between">
                    <div>
                        <CoinDisplay coins={payment.total_amount_display} size="sm" />
                        {payment.reason && <p className="text-xs text-muted-foreground italic mt-0.5">{payment.reason}</p>}
                        <p className="text-[10px] text-muted-foreground mt-0.5">by {payment.creator_name || "DM"}</p>
                        {payment.receiver_name && (
                            <p className="text-[10px] text-success mt-0.5">→ pays {payment.receiver_name}</p>
                        )}
                    </div>
                    <Badge className="bg-warning-soft text-warning border-warning/30 text-[10px]">Pending</Badge>
                </div>

                {/* Non-participant notice */}
                {!isParticipant && !isDM && (
                    <p className="text-[10px] text-muted-foreground italic">You are not part of this split</p>
                )}

                <div className="space-y-2">
                    {payment.participants.map((p) => (
                        <div key={p.character_id} className="rounded-md border border-border/30 bg-secondary/10 px-2.5 py-2">
                            <div className="flex items-center justify-between gap-2">
                                <div className="min-w-0 flex items-center gap-2">
                                    <span className="truncate text-xs font-medium">{p.character_name}</span>
                                    <span
                                        className={`inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-semibold ${p.has_accepted
                                            ? "border-success/35 bg-success-soft text-success"
                                            : "border-warning/35 bg-warning-soft text-warning"
                                            }`}
                                    >
                                        {p.has_accepted ? "✓ Accepted" : "… Pending"}
                                    </span>
                                </div>
                                <CoinDisplay coins={p.share_display} size="sm" />
                            </div>
                        </div>
                    ))}
                </div>

                {needsMyAction && (
                    <div className="flex gap-2 mt-2">
                        <Button size="sm" className="flex-1 h-9 bg-success-soft text-success hover:opacity-90 border border-success/35 flex items-center gap-1.5"
                            onClick={() => onAction(payment.id, "accept")}><Check className="w-3.5 h-3.5" /> Accept</Button>
                        <Button size="sm" variant="outline" className="flex-1 h-9 text-danger border-danger/40 hover:bg-danger-soft flex items-center gap-1.5"
                            onClick={() => onAction(payment.id, "reject")}><X className="w-3.5 h-3.5" /> Reject</Button>
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
    const labels: Record<string, { icon: React.ElementType; label: string; color: string }> = {
        transfer: { icon: ArrowUpRight, label: "Transfer", color: "text-info" },
        dm_grant: { icon: CircleDollarSign, label: "DM Loot", color: "text-success" },
        dm_deduct: { icon: Zap, label: "DM Deduct", color: "text-danger" },
        joint_payment: { icon: Handshake, label: "Split", color: "text-warning" },
        spend: { icon: Store, label: "NPC Purchase", color: "text-copper" },
        self_add: { icon: Plus, label: "Self Add", color: "text-success" },
    };

    if (transactions.length === 0) {
        return <EmptyState icon="scroll" message="No tales to tell yet — make your first transaction!" />;
    }

    return (
        <div className="space-y-1">
            {transactions.map((txn) => {
                const info = labels[txn.transaction_type] || labels.transfer;
                return (
                    <div key={txn.id} className="flex items-start justify-between py-2.5 px-3 rounded-lg border border-border/50 bg-card/70 hover:bg-card transition-colors">
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                                <info.icon className={`w-3.5 h-3.5 ${info.color}`} />
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
    );
}

/* ============================================
   PARTY SETTINGS
   ============================================ */

function PartySettings({
    partyCode, party, isDM, myCharacter, onRefresh, onBack,
}: {
    partyCode: string; party: PartyDetail; isDM: boolean; myCharacter: CharacterInParty | undefined; onRefresh: () => void; onBack: () => void;
}) {
    const [saving, setSaving] = useState(false);
    const myCoinSettings = party.my_coin_settings ?? {
        use_gold: party.use_gold,
        use_electrum: party.use_electrum,
        use_platinum: party.use_platinum,
    };

    const toggleCoin = async (coin: "use_gold" | "use_electrum" | "use_platinum", val: boolean) => {
        setSaving(true);
        try {
            await partyApi.updateMyCoins(partyCode, { [coin]: val });
            toast.success("Updated!"); onRefresh();
        } catch { toast.error("Failed"); }
        finally { setSaving(false); }
    };

    const toggleBalanceVisibility = async (val: boolean) => {
        setSaving(true);
        try {
            await partyApi.updateMyCharacterSettings(partyCode, { is_balance_public: val });
            toast.success("Updated!"); onRefresh();
        } catch {
            toast.error("Failed");
        } finally {
            setSaving(false);
        }
    };

    return (
        <Card className="card-medieval border-dnd-red/20 mt-4">
            <CardHeader className="pb-3">
                <CardTitle className="text-base text-dnd-red flex gap-2 items-center"><Settings className="w-5 h-5" /> Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="space-y-1.5">
                    <Label className="text-xs text-muted-foreground">My Coins</Label>
                    <div className="flex flex-wrap gap-1.5">
                        {([["use_gold", myCoinSettings.use_gold, "Gold", "text-gold", CircleDollarSign] as const,
                        ["use_electrum", myCoinSettings.use_electrum, "Electrum", "text-electrum", Zap] as const,
                        ["use_platinum", myCoinSettings.use_platinum, "Platinum", "text-platinum", Gem] as const,
                        ]).map(([key, on, label, color, Icon]) => (
                            <button key={key} disabled={saving} onClick={() => toggleCoin(key, !on)}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium transition-all border ${on ? `bg-primary/20 ${color} border-current/30` : "bg-secondary/30 text-muted-foreground border-transparent hover:border-border/50"}`}>
                                <Icon className="w-3.5 h-3.5" />
                                {label}
                            </button>
                        ))}
                    </div>
                    <p className="text-[10px] text-muted-foreground">Silver & Copper always on</p>
                </div>
                {myCharacter && (
                    <div className="space-y-1.5">
                        <Label className="text-xs text-muted-foreground">Wallet Visibility</Label>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={myCharacter.is_balance_public}
                            disabled={saving}
                            onClick={() => toggleBalanceVisibility(!myCharacter.is_balance_public)}
                            className="w-full rounded-md border border-border/50 bg-secondary/20 px-3 py-2 transition-all hover:border-border/80"
                        >
                            <div className="flex items-center justify-between gap-3">
                                <div className="text-left">
                                    <p className="text-xs font-semibold text-foreground">
                                        {myCharacter.is_balance_public ? "Public to party" : "Private to party"}
                                    </p>
                                    <p className="text-[10px] text-muted-foreground">
                                        {myCharacter.is_balance_public
                                            ? "Other players can see your funds"
                                            : "Other players will see Hidden"}
                                    </p>
                                </div>
                                <span
                                    className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${myCharacter.is_balance_public ? "bg-success/70" : "bg-border"
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${myCharacter.is_balance_public ? "translate-x-4" : "translate-x-0.5"
                                            }`}
                                    />
                                </span>
                            </div>
                        </button>
                        <p className="text-[10px] text-muted-foreground">DM can always see all balances.</p>
                    </div>
                )}
                {isDM && party.is_active && (
                    <>
                        <Separator className="bg-border/20" />
                    <Button variant="outline" size="sm"
                        className="w-full text-destructive border-destructive/30 hover:bg-destructive/10 h-9 text-xs flex items-center justify-center gap-2"
                        onClick={async () => {
                            if (!confirm("Archive this party?")) return;
                            try { await partyApi.archive(partyCode); toast.success("Archived"); onBack(); }
                            catch { toast.error("Failed"); }
                        }}>
                        <Archive className="w-4 h-4" /> Archive Party
                    </Button>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
