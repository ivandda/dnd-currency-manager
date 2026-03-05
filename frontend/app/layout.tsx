import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "D&D Currency Manager",
  description: "Real-time currency management for Dungeons & Dragons parties on LAN",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-parchment antialiased">
        <AuthProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "oklch(0.2 0.02 55)",
                color: "oklch(0.88 0.04 75)",
                border: "1px solid oklch(0.32 0.06 65 / 40%)",
              },
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
