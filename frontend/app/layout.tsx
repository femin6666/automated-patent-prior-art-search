import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PatentLens AI | Semantic Prior-Art Discovery Platform",
  description: "AI-Powered Semantic Prior-Art Discovery for Innovators, Startups, Students & MSME Researchers.",
  keywords: ["Patent Search", "Prior Art", "AI Patent", "SBERT", "pgvector", "PatentLens AI"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className={`${inter.className} bg-slate-950 text-slate-100 antialiased selection:bg-blue-500 selection:text-white`}>
        {children}
      </body>
    </html>
  );
}
