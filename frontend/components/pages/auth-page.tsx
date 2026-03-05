"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";

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
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-md animate-slide-up">
                {/* Title */}
                <div className="text-center mb-8">
                    <h1 className="text-5xl font-bold text-dnd-red glow-red tracking-wide">
                        ⚔️
                    </h1>
                    <h2 className="text-3xl font-bold text-dnd-red glow-red mt-2 tracking-wide">
                        D&D Currency
                    </h2>
                    <h2 className="text-3xl font-bold text-dnd-red glow-red tracking-wide">
                        Manager
                    </h2>
                    <p className="text-muted-foreground mt-2 text-lg italic">
                        &ldquo;Every coin tells a tale...&rdquo;
                    </p>
                </div>

                <Card className="card-medieval">
                    <Tabs defaultValue="login">
                        <TabsList className="grid w-full grid-cols-2 bg-secondary/30">
                            <TabsTrigger value="login" className="data-[state=active]:bg-primary/20 data-[state=active]:text-dnd-red">
                                Enter the Tavern
                            </TabsTrigger>
                            <TabsTrigger value="register" className="data-[state=active]:bg-primary/20 data-[state=active]:text-dnd-red">
                                Create Account
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="login">
                            <form onSubmit={handleLogin}>
                                <CardHeader>
                                    <CardTitle className="text-dnd-red text-xl">Welcome Back</CardTitle>
                                    <CardDescription>Sign in to manage your fortune</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="login-username">Username</Label>
                                        <Input
                                            id="login-username"
                                            placeholder="Your adventurer name"
                                            value={loginUsername}
                                            onChange={(e) => setLoginUsername(e.target.value)}
                                            className="bg-secondary/30 border-border/50"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="login-password">Password</Label>
                                        <Input
                                            id="login-password"
                                            type="password"
                                            placeholder="••••••••"
                                            value={loginPassword}
                                            onChange={(e) => setLoginPassword(e.target.value)}
                                            className="bg-secondary/30 border-border/50"
                                            required
                                        />
                                    </div>
                                    <Button
                                        type="submit"
                                        className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-base"
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? "Entering..." : "⚔️ Enter"}
                                    </Button>
                                </CardContent>
                            </form>
                        </TabsContent>

                        <TabsContent value="register">
                            <form onSubmit={handleRegister}>
                                <CardHeader>
                                    <CardTitle className="text-dnd-red text-xl">New Adventurer</CardTitle>
                                    <CardDescription>Create your account to begin</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="reg-username">Username</Label>
                                        <Input
                                            id="reg-username"
                                            placeholder="Choose a name (min 3 chars)"
                                            value={regUsername}
                                            onChange={(e) => setRegUsername(e.target.value)}
                                            className="bg-secondary/30 border-border/50"
                                            minLength={3}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="reg-password">Password</Label>
                                        <Input
                                            id="reg-password"
                                            type="password"
                                            placeholder="Minimum 6 characters"
                                            value={regPassword}
                                            onChange={(e) => setRegPassword(e.target.value)}
                                            className="bg-secondary/30 border-border/50"
                                            minLength={6}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="reg-confirm">Confirm Password</Label>
                                        <Input
                                            id="reg-confirm"
                                            type="password"
                                            placeholder="Repeat your password"
                                            value={regConfirm}
                                            onChange={(e) => setRegConfirm(e.target.value)}
                                            className="bg-secondary/30 border-border/50"
                                            required
                                        />
                                    </div>
                                    <Button
                                        type="submit"
                                        className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-base"
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? "Creating..." : "📜 Register"}
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
