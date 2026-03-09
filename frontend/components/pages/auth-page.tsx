"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Swords, Scroll, LogIn } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

export default function AuthPage() {
    const { login, register } = useAuth();
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Login form
    const [loginUsername, setLoginUsername] = useState("");
    const [loginPassword, setLoginPassword] = useState("");

    // Register form
    const [regUsername, setRegUsername] = useState("");
    const [regPassword, setRegPassword] = useState("");
    const [regConfirm, setRegConfirm] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await login(loginUsername, loginPassword);
            toast.success("Welcome back, adventurer!");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Login failed";
            toast.error(message);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        if (regPassword !== regConfirm) {
            toast.error("Passwords do not match!");
            return;
        }
        if (regPassword.length < 6) {
            toast.error("Password must be at least 6 characters");
            return;
        }
        setIsSubmitting(true);
        try {
            await register(regUsername, regPassword);
            toast.success("Account created! Welcome to the realm!");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Registration failed";
            toast.error(message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="relative min-h-screen px-4 py-8 md:px-8">
            <div className="absolute top-4 right-4 animate-fade-in">
                <ThemeToggle />
            </div>

            <div className="mx-auto grid w-full max-w-6xl items-stretch gap-6 lg:grid-cols-[1.05fr_1fr]">
                <section className="hidden lg:flex animate-slide-up rounded-2xl border border-border/40 bg-card/40 p-10 backdrop-blur-sm">
                    <div className="flex h-full flex-col justify-between">
                        <div>
                            <div className="mb-5 text-dnd-red glow-red">
                                <Swords className="h-16 w-16" strokeWidth={1.5} />
                            </div>
                            <h1 className="text-4xl font-bold leading-tight text-dnd-red glow-red tracking-wide">
                                D&D Currency Manager
                            </h1>
                            <p className="mt-4 max-w-md text-base text-muted-foreground">
                                Run a clean party economy in real time: track wallets, split costs, and keep every coin movement logged.
                            </p>
                        </div>
                        <div className="rounded-xl border border-border/30 bg-background/50 p-4 text-sm text-muted-foreground">
                            Share your party link, invite players on LAN, and keep everyone synced instantly.
                        </div>
                    </div>
                </section>

                <div className="w-full max-w-md lg:max-w-none lg:self-center lg:justify-self-end animate-slide-up">
                    <div className="text-center mb-10 flex flex-col items-center lg:hidden">
                        <div className="mb-4 text-dnd-red glow-red">
                            <Swords className="w-16 h-16" strokeWidth={1.5} />
                        </div>
                        <h2 className="text-3xl font-bold text-dnd-red glow-red tracking-wide">
                            D&D Currency
                        </h2>
                        <h2 className="text-3xl font-bold text-dnd-red glow-red tracking-wide">
                            Manager
                        </h2>
                        <p className="text-muted-foreground mt-4 text-lg italic tracking-wide">
                            &ldquo;Every coin tells a tale...&rdquo;
                        </p>
                    </div>

                    <Tabs defaultValue="login" className="w-full">
                        <TabsList className="flex w-full bg-transparent p-0 gap-1 sm:gap-2 h-12">
                            <TabsTrigger value="login" className="flex-1 rounded-t-xl rounded-b-none bg-secondary/30 data-[state=active]:bg-card data-[state=active]:text-dnd-red transition-all text-sm sm:text-base h-full shadow-none border border-transparent data-[state=active]:border-border/40 data-[state=active]:border-b-card relative top-[1px] z-10 font-bold">
                                Enter the Tavern
                            </TabsTrigger>
                            <TabsTrigger value="register" className="flex-1 rounded-t-xl rounded-b-none bg-secondary/30 data-[state=active]:bg-card data-[state=active]:text-dnd-red transition-all text-sm sm:text-base h-full shadow-none border border-transparent data-[state=active]:border-border/40 data-[state=active]:border-b-card relative top-[1px] z-10 font-bold">
                                Create Account
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="login" className="mt-0">
                            <Card className="card-medieval border-t border-border/40 rounded-t-none relative z-0 shadow-lg">
                                <form onSubmit={handleLogin}>
                                    <CardHeader className="pb-8 text-center pt-8">
                                        <CardTitle className="text-dnd-red text-2xl">Welcome Back</CardTitle>
                                        <CardDescription className="text-base text-muted-foreground mt-2">Sign in to manage your fortune</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="space-y-3">
                                            <Label htmlFor="login-username" className="text-base font-semibold">Username</Label>
                                            <Input
                                                id="login-username"
                                                placeholder="Your adventurer name"
                                                value={loginUsername}
                                                onChange={(e) => setLoginUsername(e.target.value)}
                                                className="bg-secondary/20 border-border/60 focus:border-border placeholder:text-muted-foreground/50 h-12 text-base"
                                                autoCapitalize="none"
                                                autoCorrect="off"
                                                required
                                            />
                                        </div>
                                        <div className="space-y-3 pb-2">
                                            <Label htmlFor="login-password" className="text-base font-semibold">Password</Label>
                                            <Input
                                                id="login-password"
                                                type="password"
                                                placeholder="••••••••"
                                                value={loginPassword}
                                                onChange={(e) => setLoginPassword(e.target.value)}
                                                className="bg-secondary/20 border-border/60 focus:border-border placeholder:text-muted-foreground/50 h-12 text-base"
                                                required
                                            />
                                        </div>
                                        <Button
                                            type="submit"
                                            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-lg h-12 flex items-center justify-center gap-2 transition-transform active:scale-[0.98]"
                                            disabled={isSubmitting}
                                        >
                                            {isSubmitting ? "Entering..." : <><LogIn className="w-5 h-5" /> Enter</>}
                                        </Button>
                                    </CardContent>
                                </form>
                            </Card>
                        </TabsContent>

                        <TabsContent value="register" className="mt-0">
                            <Card className="card-medieval border-t border-border/40 rounded-t-none relative z-0 shadow-lg">
                                <form onSubmit={handleRegister}>
                                    <CardHeader className="pb-8 text-center pt-8">
                                        <CardTitle className="text-dnd-red text-2xl">New Adventurer</CardTitle>
                                        <CardDescription className="text-base text-muted-foreground mt-2">Create your account to begin</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="space-y-3">
                                            <Label htmlFor="reg-username" className="text-base font-semibold">Username</Label>
                                            <Input
                                                id="reg-username"
                                                placeholder="Choose a name (min 3 chars)"
                                                value={regUsername}
                                                onChange={(e) => setRegUsername(e.target.value)}
                                                className="bg-secondary/20 border-border/60 focus:border-border placeholder:text-muted-foreground/50 h-12 text-base"
                                                autoCapitalize="none"
                                                autoCorrect="off"
                                                minLength={3}
                                                required
                                            />
                                        </div>
                                        <div className="space-y-3">
                                            <Label htmlFor="reg-password" className="text-base font-semibold">Password</Label>
                                            <Input
                                                id="reg-password"
                                                type="password"
                                                placeholder="Minimum 6 characters"
                                                value={regPassword}
                                                onChange={(e) => setRegPassword(e.target.value)}
                                                className="bg-secondary/20 border-border/60 focus:border-border placeholder:text-muted-foreground/50 h-12 text-base"
                                                minLength={6}
                                                required
                                            />
                                        </div>
                                        <div className="space-y-3 pb-2">
                                            <Label htmlFor="reg-confirm" className="text-base font-semibold">Confirm Password</Label>
                                            <Input
                                                id="reg-confirm"
                                                type="password"
                                                placeholder="Repeat your password"
                                                value={regConfirm}
                                                onChange={(e) => setRegConfirm(e.target.value)}
                                                className="bg-secondary/20 border-border/60 focus:border-border placeholder:text-muted-foreground/50 h-12 text-base"
                                                required
                                            />
                                        </div>
                                        <Button
                                            type="submit"
                                            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-lg h-12 flex items-center justify-center gap-2 transition-transform active:scale-[0.98]"
                                            disabled={isSubmitting}
                                        >
                                            {isSubmitting ? "Creating..." : <><Scroll className="w-5 h-5" /> Register</>}
                                        </Button>
                                    </CardContent>
                                </form>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}
