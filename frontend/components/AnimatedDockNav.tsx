"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Home, Search, Layers, User, Zap, Sparkles } from "lucide-react";

export interface DockNavItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

export interface AnimatedDockNavProps {
  items?: DockNavItem[];
  activeId?: string;
  onSelect?: (id: string) => void;
  className?: string;
}

const DEFAULT_DOCK_ITEMS: DockNavItem[] = [
  { id: "profile", label: "Profile", href: "/profile", icon: User },
  { id: "features", label: "Features", href: "#features", icon: Zap },
  { id: "search", label: "Search", href: "#search", icon: Search },
  { id: "how-it-works", label: "How It Works", href: "#how-it-works", icon: Layers },
  { id: "home", label: "Home", href: "/", icon: Home },
];

const AnimatedDockNav: React.FC<AnimatedDockNavProps> = ({
  items = DEFAULT_DOCK_ITEMS,
  activeId = "profile",
  onSelect,
  className = "",
}) => {
  const [selectedTab, setSelectedTab] = useState(activeId);

  const handleSelect = (id: string) => {
    setSelectedTab(id);
    if (onSelect) {
      onSelect(id);
    }
  };

  return (
    <div
      className={`relative inline-flex items-center gap-1.5 sm:gap-4 px-4 sm:px-6 py-2.5 rounded-2xl sm:rounded-full bg-[#121214]/95 border border-white/10 shadow-[0_15px_40px_rgba(0,0,0,0.85),0_0_20px_rgba(0,0,0,0.5)] backdrop-blur-2xl ${className}`}
    >
      {items.map((item) => {
        const isActive = selectedTab === item.id;
        const Icon = item.icon;

        return (
          <Link
            key={item.id}
            href={item.href}
            onClick={() => handleSelect(item.id)}
            className="relative flex flex-col items-center justify-center px-3 py-1.5 transition-colors cursor-pointer select-none group min-w-[54px]"
          >
            {/* Active Orange/Amber Spotlight Backlight Glow (Matches User Image) */}
            {isActive && (
              <motion.div
                layoutId="dockGlow"
                className="absolute inset-0 bg-gradient-to-t from-orange-500/35 via-amber-500/15 to-transparent rounded-xl blur-md -z-10"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}

            {/* Nav Icon */}
            <motion.div
              animate={{
                scale: isActive ? 1.25 : 1,
                y: isActive ? -2 : 0,
              }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className="flex items-center justify-center"
            >
              <Icon
                className={`w-5 h-5 transition-colors duration-200 ${
                  isActive
                    ? "text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"
                    : "text-zinc-400 group-hover:text-zinc-200"
                }`}
              />
            </motion.div>

            {/* Active Label Underneath Icon (Matches User Image) */}
            {isActive && (
              <motion.span
                initial={{ opacity: 0, y: 4, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 4, scale: 0.8 }}
                transition={{ duration: 0.2 }}
                className="text-[11px] font-semibold text-amber-200 tracking-wide mt-1 leading-none shadow-sm"
              >
                {item.label}
              </motion.span>
            )}

            {/* Active Bottom Orange Indicator Pill Tag (Matches User Image) */}
            {isActive && (
              <motion.div
                layoutId="dockPill"
                className="absolute -bottom-2.5 w-7 h-1.5 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-400 rounded-full shadow-[0_0_12px_#f97316]"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
          </Link>
        );
      })}
    </div>
  );
};

export default AnimatedDockNav;
