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
        <div className="relative min-h-screen flex items-center justify-center p-4">
            <div className="absolute top-4 right-4 animate-fade-in">
                <ThemeToggle />
            </div>

            <div className="w-full max-w-md animate-slide-up">
                {/* Title */}
                <div className="text-center mb-10 flex flex-col items-center">
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

                <Card className="card-medieval">
                    <Tabs defaultValue="login">
                        <TabsList className="grid w-full grid-cols-2 bg-secondary/30">
                            <TabsTrigger value="login" className="data-[state=active]:bg-primary/20 data-[state=active]:text-dnd-red transition-all">
                                Enter the Tavern
                            </TabsTrigger>
                            <TabsTrigger value="register" className="data-[state=active]:bg-primary/20 data-[state=active]:text-dnd-red transition-all">
                                Create Account
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="login">
                            <form onSubmit={handleLogin}>
                                <CardHeader className="pb-8 text-center pt-6">
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
                        </TabsContent>

                        <TabsContent value="register">
                            <form onSubmit={handleRegister}>
                                <CardHeader className="pb-8 text-center pt-6">
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
                        </TabsContent>
                    </Tabs>
                </Card>
            </div>
        </div>
    );
}
