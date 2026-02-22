import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ChatBotAI - AI Chatbots for Small Businesses",
  description: "Transform your customer service with intelligent AI chatbots. Help small businesses provide 24/7 support, boost engagement, and increase sales with our easy-to-use chatbot solutions.",
  keywords: ["AI chatbot", "customer service", "small business", "automation", "chatbot", "artificial intelligence"],
  authors: [{ name: "ChatBotAI Team" }],
  openGraph: {
    title: "ChatBotAI - AI Chatbots for Small Businesses",
    description: "Transform your customer service with intelligent AI chatbots for small businesses.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "ChatBotAI - AI Chatbots for Small Businesses",
    description: "Transform your customer service with intelligent AI chatbots for small businesses.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          {children}
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}
