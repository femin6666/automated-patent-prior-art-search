"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import RiskBadge from "@/components/RiskBadge";
import {
  Search,
  Bookmark,
  FileText,
  TrendingUp,
  ArrowUpRight,
  PlusCircle,
  History,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { api } from "@/services/api";
import { SearchHistoryItem, SavedPatent, Report, User } from "@/types";
import { formatDate } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [saved, setSaved] = useState<SavedPatent[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const u = await api.getMe();
        setUser(u);
        const [h, s, r] = await Promise.all([
          api.getSearchHistory(),
          api.getSavedPatents(),
          api.getReports(),
        ]);
        setHistory(h);
        setSaved(s);
        setReports(r);
      } catch (err) {
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  const totalSearches = history.length;
  const savedCount = saved.length;
  const reportsCount = reports.length;
  const highestSim = history.length > 0
    ? Math.max(...history.map((item) => item.highest_similarity))
    : 0;

  const chartData = history.slice(0, 7).reverse().map((h) => ({
    title: h.invention_title.length > 15 ? h.invention_title.substring(0, 15) + "..." : h.invention_title,
    score: h.highest_similarity,
  }));

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-7xl mx-auto space-y-8">
          
          {/* Header & Welcome */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
            <div>
              <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">
                Welcome back, <span className="text-indigo-400">{user?.name || "Innovator"}</span> 👋
              </h1>
              <p className="text-xs text-zinc-400 mt-1">
                Overview of your AI prior-art searches and saved patent intelligence.
              </p>
            </div>
            
            <Link
              href="/search"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Start New Search</span>
            </Link>
          </div>

          {/* Metric Stats Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Stat 1 */}
            <div className="p-5 rounded-xl tech-card tech-card-hover flex items-center justify-between">
              <div>
                <div className="text-[10px] font-mono font-medium text-zinc-500 uppercase tracking-wider">Total Searches</div>
                <div className="text-2xl font-mono font-bold text-zinc-100 mt-1">{totalSearches}</div>
              </div>
              <div className="w-9 h-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                <Search className="w-4 h-4" />
              </div>
            </div>

            {/* Stat 2 */}
            <div className="p-5 rounded-xl tech-card tech-card-hover flex items-center justify-between">
              <div>
                <div className="text-[10px] font-mono font-medium text-zinc-500 uppercase tracking-wider">Saved Patents</div>
                <div className="text-2xl font-mono font-bold text-zinc-100 mt-1">{savedCount}</div>
              </div>
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                <Bookmark className="w-4 h-4" />
              </div>
            </div>

            {/* Stat 3 */}
            <div className="p-5 rounded-xl tech-card tech-card-hover flex items-center justify-between">
              <div>
                <div className="text-[10px] font-mono font-medium text-zinc-500 uppercase tracking-wider">Reports Generated</div>
                <div className="text-2xl font-mono font-bold text-zinc-100 mt-1">{reportsCount}</div>
              </div>
              <div className="w-9 h-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                <FileText className="w-4 h-4" />
              </div>
            </div>

            {/* Stat 4 */}
            <div className="p-5 rounded-xl tech-card tech-card-hover flex items-center justify-between">
              <div>
                <div className="text-[10px] font-mono font-medium text-zinc-500 uppercase tracking-wider">Highest Similarity</div>
                <div className="text-2xl font-mono font-bold text-indigo-400 mt-1">{highestSim}%</div>
              </div>
              <div className="w-9 h-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>

          </div>

          {/* Quick Actions & Recharts Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Recent Searches Table */}
            <div className="lg:col-span-2 p-6 rounded-xl tech-card space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-zinc-100">Recent Prior-Art Searches</h3>
                  <p className="text-xs text-zinc-400">Latest invention submissions and similarity scores.</p>
                </div>
                <Link
                  href="/history"
                  className="text-xs font-mono font-medium text-indigo-400 hover:underline flex items-center gap-1"
                >
                  <span>View All</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {history.length === 0 ? (
                <div className="py-12 text-center text-zinc-500 space-y-3">
                  <Sparkles className="w-6 h-6 mx-auto text-zinc-600" />
                  <p className="text-xs">No prior-art searches conducted yet.</p>
                  <Link
                    href="/search"
                    className="inline-block px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium shadow-sm shadow-indigo-500/20"
                  >
                    Start Your First Search
                  </Link>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider">
                        <th className="pb-2.5 pr-4">Invention Title</th>
                        <th className="pb-2.5 pr-4">Domain</th>
                        <th className="pb-2.5 pr-4">Date</th>
                        <th className="pb-2.5 pr-4 text-right">Highest Sim</th>
                        <th className="pb-2.5 text-right whitespace-nowrap">Risk Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/60">
                      {history.slice(0, 5).map((item) => (
                        <tr key={item.id} className="hover:bg-zinc-900/60 transition-colors">
                          <td className="py-3 font-semibold text-zinc-100 max-w-[200px] sm:max-w-xs truncate pr-4" title={item.invention_title}>
                            <Link href={`/search/${item.id}`} className="hover:text-indigo-400 transition-colors">
                              {item.invention_title}
                            </Link>
                          </td>
                          <td className="py-3 text-zinc-300 font-medium whitespace-nowrap pr-4">{item.domain}</td>
                          <td className="py-3 text-zinc-400 font-mono text-[11px] whitespace-nowrap pr-4">{formatDate(item.created_at)}</td>
                          <td className="py-3 text-right font-mono font-bold text-indigo-400 whitespace-nowrap pr-4">
                            {item.highest_similarity}%
                          </td>
                          <td className="py-3 text-right whitespace-nowrap">
                            <RiskBadge level={item.risk_level} size="sm" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Quick Actions & Recent Analytics */}
            <div className="space-y-6">
              
              {/* Quick Actions */}
              <div className="p-6 rounded-xl tech-card space-y-3">
                <h3 className="text-base font-bold text-zinc-100">Quick Actions</h3>
                <div className="space-y-2">
                  <Link
                    href="/search"
                    className="w-full flex items-center justify-between p-3 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 text-xs font-medium transition-all"
                  >
                    <div className="flex items-center gap-2.5">
                      <PlusCircle className="w-4 h-4 text-indigo-400" />
                      <span>Start New Prior-Art Search</span>
                    </div>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>

                  <Link
                    href="/history"
                    className="w-full flex items-center justify-between p-3 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium transition-all border border-zinc-800"
                  >
                    <div className="flex items-center gap-2.5">
                      <History className="w-4 h-4 text-zinc-400" />
                      <span>View Search History</span>
                    </div>
                    <ArrowUpRight className="w-3.5 h-3.5 text-zinc-500" />
                  </Link>

                  <Link
                    href="/saved"
                    className="w-full flex items-center justify-between p-3 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium transition-all border border-zinc-800"
                  >
                    <div className="flex items-center gap-2.5">
                      <Bookmark className="w-4 h-4 text-zinc-400" />
                      <span>View Saved Patents</span>
                    </div>
                    <ArrowUpRight className="w-3.5 h-3.5 text-zinc-500" />
                  </Link>
                </div>
              </div>

              {/* Recharts Analytics Chart */}
              <div className="p-6 rounded-xl tech-card space-y-3">
                <h3 className="text-base font-bold text-zinc-100">Recent Similarity Scores</h3>
                {chartData.length === 0 ? (
                  <p className="text-xs text-zinc-500 text-center py-6">No search data available for chart visualization.</p>
                ) : (
                  <div className="h-44">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="title" stroke="#71717a" fontSize={10} tickLine={false} />
                        <YAxis stroke="#71717a" fontSize={10} domain={[0, 100]} unit="%" />
                        <Tooltip
                          contentStyle={{
                            background: "#0d0e15",
                            borderColor: "rgba(255, 255, 255, 0.1)",
                            borderRadius: "8px",
                            fontSize: "11px"
                          }}
                        />
                        <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

            </div>

          </div>

        </div>
      </main>
    </div>
  );
}
