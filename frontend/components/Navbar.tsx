"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ThemeToggle from "./ThemeToggle";
import { Search, UserCheck } from "lucide-react";
import { api } from "@/services/api";
import PillNav from "./PillNav";

export default function Navbar() {
  const [user, setUser] = useState<any>(null);
  const [activeHref, setActiveHref] = useState("#how-it-works");
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => setUser(null));

    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navItems = [
    { label: "Home", href: "/" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Features", href: "#features" },
    { label: "About", href: "#about" },
    { label: "Pricing", href: "#pricing" },
    { label: "FAQ", href: "#faq" },
  ];

  return (
    <header className={`sticky z-50 transition-all duration-300 ${
      isScrolled ? "top-3 px-4 sm:px-6 lg:px-8" : "top-0 w-full"
    }`}>
      <div className={`transition-all duration-300 flex items-center justify-between ${
        isScrolled
          ? "max-w-6xl mx-auto px-6 py-2 bg-[#090c24]/95 backdrop-blur-2xl border border-indigo-500/40 rounded-full shadow-[0_10px_35px_rgba(0,0,0,0.85),0_0_25px_rgba(99,102,241,0.25)]"
          : "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 bg-[#060713]/90 backdrop-blur-xl border-b border-white/10"
      }`}>
        
        {/* Far Left Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-0.5 shadow-[0_0_20px_rgba(99,102,241,0.5)] group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#070817] rounded-[10px] flex items-center justify-center">
              <span className="text-cyan-400 font-bold text-lg">✦</span>
            </div>
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-lg text-white tracking-tight leading-none flex items-center gap-1">
              PriorArt<span className="text-indigo-400">IQ</span>
            </span>
            <span className="text-[10px] text-zinc-400 font-medium tracking-wide">
              Patent Search, Smarter.
            </span>
          </div>
        </Link>

        {/* Centered Navigation Pills (React Bits PillNav) */}
        <div className="hidden md:flex items-center justify-center">
          <PillNav
            items={navItems}
            activeHref={activeHref}
            baseColor="#818cf8"
            pillColor="rgba(255, 255, 255, 0.06)"
            pillTextColor="#94a3b8"
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
              className="flex items-center gap-2 px-5 py-2 rounded-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:opacity-90 text-white font-bold text-xs shadow-lg shadow-indigo-500/30 transition-all"
            >
              <UserCheck className="w-4 h-4" />
              <span>Dashboard</span>
            </Link>
          ) : (
            <div className="flex items-center gap-2.5">
              <Link
                href="/login"
                className="px-5 py-2 rounded-full bg-white/[0.05] border border-white/15 hover:bg-white/10 text-xs font-semibold text-zinc-200 transition-all"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="px-5 py-2 rounded-full bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-xs font-bold text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all flex items-center gap-1.5"
              >
                <span>Get Started</span>
                <span className="text-sm">→</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
