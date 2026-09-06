"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ThemeToggle from "./ThemeToggle";
import { Home, Search, Layers, User, Zap } from "lucide-react";
import { api } from "@/services/api";
import AnimatedDockNav, { DockNavItem } from "./AnimatedDockNav";

export default function Navbar() {
  const [user, setUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("home");

  useEffect(() => {
    api.getMe().then(setUser).catch(() => setUser(null));
  }, []);

  const dockNavItems: DockNavItem[] = [
    { id: "home", label: "Home", href: "/", icon: Home },
    { id: "how-it-works", label: "How It Works", href: "#how-it-works", icon: Layers },
    { id: "search", label: "Search", href: "#search", icon: Search },
    { id: "features", label: "Features", href: "#features", icon: Zap },
    { id: "profile", label: user ? "Dashboard" : "Account", href: user ? "/dashboard" : "/login", icon: User },
  ];

  return (
    <header className="fixed top-3 left-0 right-0 z-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto px-6 py-2.5 bg-[#090c24]/95 backdrop-blur-2xl border border-indigo-500/50 rounded-full shadow-[0_15px_45px_rgba(0,0,0,0.95),0_0_30px_rgba(99,102,241,0.3)] flex items-center justify-between transition-all duration-300">
        
        {/* Far Left Brand Logo with Curved Base */}
        <Link href="/" className="flex items-center gap-3 group shrink-0">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-0.5 shadow-[0_0_20px_rgba(99,102,241,0.5)] group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#070817] rounded-full flex items-center justify-center">
              <span className="text-cyan-400 font-bold text-lg">✦</span>
            </div>
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-base text-white tracking-tight leading-none flex items-center gap-1">
              PriorArt<span className="text-indigo-400">IQ</span>
            </span>
            <span className="text-[9px] text-zinc-400 font-medium tracking-wide">
              Patent Search, Smarter.
            </span>
          </div>
        </Link>

        {/* Centered Animated Dock Navigation Bar */}
        <div className="flex items-center justify-center mx-2">
          <AnimatedDockNav
            items={dockNavItems}
            activeId={activeTab}
            onSelect={setActiveTab}
          />
        </div>

        {/* Far Right Rounded Theme Toggle End */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-9 h-9 rounded-full bg-white/[0.04] border border-white/10 flex items-center justify-center hover:bg-white/[0.08] transition-all">
            <ThemeToggle />
          </div>
        </div>

      </div>
    </header>
  );
}
