"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ThemeToggle from "./ThemeToggle";
import { Search, UserCheck } from "lucide-react";
import { api } from "@/services/api";
import PillNav from "./PillNav";

export default function Navbar() {
  const [user, setUser] = useState<any>(null);
  const [activeHref, setActiveHref] = useState("#technology");

  useEffect(() => {
    api.getMe().then(setUser).catch(() => setUser(null));
  }, []);

  const navItems = [
    { label: "How It Works", href: "#how-it-works" },
    { label: "Technology", href: "#technology" },
    { label: "About", href: "#about" },
    { label: "Pricing", href: "#pricing" },
  ];

  return (
    <header className="sticky top-0 z-50 py-3 bg-[#070814]/90 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        
        {/* Far Left Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/60 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform shadow-[0_0_15px_rgba(99,102,241,0.4)]">
            <Search className="w-4 h-4 text-indigo-400" />
          </div>
          <span className="font-bold text-lg text-white tracking-tight">
            PatentLens <span className="text-indigo-400">AI</span>
          </span>
        </Link>

        {/* Centered Navigation Pills (React Bits PillNav) */}
        <div className="hidden md:flex items-center justify-center">
          <PillNav
            items={navItems}
            activeHref={activeHref}
            baseColor="#6366f1"
            pillColor="transparent"
            pillTextColor="#e2e8f0"
            hoveredPillTextColor="#ffffff"
            ease="power3.easeOut"
            initialLoadAnimation={true}
          />
        </div>

        {/* Far Right Action Buttons */}
        <div className="flex items-center gap-3">
          <ThemeToggle />

          {user ? (
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:opacity-90 text-white font-bold text-xs shadow-md shadow-indigo-500/25 transition-all"
            >
              <UserCheck className="w-4 h-4" />
              <span>Dashboard</span>
            </Link>
          ) : (
            <div className="flex items-center gap-2.5">
              <Link
                href="/login"
                className="px-4 py-2 rounded-lg bg-white/[0.06] border border-white/15 hover:bg-white/10 text-xs font-semibold text-white transition-all"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition-all"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}




