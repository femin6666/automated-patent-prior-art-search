"use client";

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

const NAV_ITEMS = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "New Search", href: "/search", icon: Search },
  { name: "Search History", href: "/history", icon: History },
  { name: "Saved Patents", href: "/saved", icon: Bookmark },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Profile", href: "/profile", icon: User },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-[#0c0d12] border-r border-zinc-800/80 flex flex-col justify-between h-screen sticky top-0 text-zinc-300 select-none z-40">
      <div>
        {/* Logo */}
        <div className="p-6 border-b border-zinc-800/80 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/60 transition-all">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-tight text-zinc-100">PatentLens <span className="text-indigo-400 font-mono text-xs">AI</span></h1>
              <p className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider">Semantic Discovery</p>
            </div>
          </Link>
        </div>

        {/* Demo Badge */}
        <div className="mx-4 my-4 px-3.5 py-2 rounded-lg bg-zinc-900/80 border border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
          <span className="font-medium flex items-center gap-1.5 text-zinc-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            Demo Dataset
          </span>
          <span className="text-[10px] font-mono font-medium text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">
            100 Records
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="px-2 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-indigo-500/10 text-zinc-100 border-l-2 border-indigo-500 font-semibold pl-3"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/60 border-l-2 border-transparent"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-zinc-500"}`} />
                  <span>{item.name}</span>
                </div>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / Logout */}
      <div className="p-4 border-t border-zinc-800/80">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
