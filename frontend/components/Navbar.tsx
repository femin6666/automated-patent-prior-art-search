"use client";

import { useEffect, useState } from "react";
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
    <header className="fixed top-4 left-0 right-0 z-50 flex items-center justify-center pointer-events-none px-4">
      <div className="pointer-events-auto">
        <AnimatedDockNav
          items={dockNavItems}
          activeId={activeTab}
          onSelect={setActiveTab}
        />
      </div>
    </header>
  );
}
