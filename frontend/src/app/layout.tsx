import type { Metadata } from "next";
import { Toaster } from "sonner";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const appName = process.env.NEXT_PUBLIC_APP_NAME || "ReCloud Lead Intelligence";

export const metadata: Metadata = {
  title: appName,
  description: "Find companies with recruitment pain signals, score them, and generate outreach drafts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased">
        <AuthProvider>{children}</AuthProvider>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
