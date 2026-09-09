"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  History,
  Bookmark,
  FileText,
  User,
  LogOut,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { api } from "@/services/api";
import Folder from "@/components/Folder";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "New Search", href: "/search", icon: Search },
  { name: "Search History", href: "/history", icon: History },
  { name: "Saved Patents", href: "/saved", icon: Bookmark, isFolder: true },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Profile", href: "/profile", icon: User },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  return (
    <aside className="w-64 backdrop-blur-2xl bg-white/[0.07] border-r border-white/15 flex flex-col justify-between h-screen sticky top-0 text-white select-none z-40 shadow-2xl">
      <div>
        {/* Logo */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 p-0.5 shadow-lg shadow-indigo-500/30 group-hover:scale-105 transition-all">
              <div className="w-full h-full bg-[#0d0f2b] rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-tight text-white flex items-center gap-1">
                PatentLens <span className="text-xs font-mono font-semibold text-purple-300 bg-purple-500/20 px-1.5 py-0.5 rounded border border-purple-400/30">AI</span>
              </h1>
              <p className="text-[9px] text-purple-200/70 font-mono uppercase tracking-widest mt-0.5">Semantic Discovery</p>
            </div>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            const isSaved = item.isFolder;
            const isHovered = hoveredItem === item.name;

            return (
              <Link
                key={item.name}
                href={item.href}
                onMouseEnter={() => setHoveredItem(item.name)}
                onMouseLeave={() => setHoveredItem(null)}
                className={`flex items-center justify-between px-4 py-3 rounded-xl text-xs font-semibold transition-all duration-200 relative group/nav ${
                  isActive
                    ? "bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 border border-white/20 scale-[1.02]"
                    : "text-white/70 hover:text-white hover:bg-white/10 border border-transparent"
                }`}
              >
                <div className="flex items-center gap-3">
                  {isSaved ? (
                    <div className="w-5 h-5 flex items-center justify-center shrink-0 overflow-visible">
                      <Folder
                        color={isActive ? "#c084fc" : isHovered ? "#a855f7" : "#818cf8"}
                        size={0.28}
                        forceOpen={isHovered}
                        items={[
                          <span key="1" className="text-[7px] font-bold text-indigo-900">PAT</span>,
                          <span key="2" className="text-[7px] font-bold text-purple-900">DOC</span>,
                          <span key="3" className="text-[7px] font-bold text-cyan-900">PDF</span>
                        ]}
                      />
                    </div>
                  ) : (
                    <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-white/60"}`} />
                  )}
                  <span>{item.name}</span>
                </div>

                {isActive && <ChevronRight className="w-3.5 h-3.5 text-white/80" />}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / Logout */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold text-rose-300 hover:text-white hover:bg-rose-500/20 border border-white/10 hover:border-rose-500/30 transition-all shadow-inner"
        >
          <LogOut className="w-4 h-4 text-rose-400" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
